import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def run_ssh(host, user, password, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    if "sudo" in cmd:
        stdin.write(password + "\n")
        stdin.flush()
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

seed_script = """
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json)

echo "=== CREATING DEMO ORGANIZATIONS & SERVICES ==="
# Organization 1: fintech-group
# Service 1: billing-service
vault kv put secret/fintech-group/billing-service \\
    service="billing-service" \\
    organization="fintech-group" \\
    db_username="billing_admin" \\
    db_password="P@ssw0rd_Billing_2026!" \\
    api_token="fintech_sec_tok_84719283749" \\
    stripe_key="sk_live_51MdemoKey123"

# Service 2: auth-service
vault kv put secret/fintech-group/auth-service \\
    service="auth-service" \\
    organization="fintech-group" \\
    jwt_secret="SuperSecretJwtKeyFintech2026" \\
    admin_password="AuthMasterPassword998"

# Organization 2: agro-holding
# Service 1: iot-gateway
vault kv put secret/agro-holding/iot-gateway \\
    service="iot-gateway" \\
    organization="agro-holding" \\
    mqtt_broker="mqtt://192.168.86.130:1883" \\
    mqtt_user="sensor_collector" \\
    mqtt_password="SensorSecurePass778" \\
    device_token="agro_iot_token_991823"

echo "=== CREATING POLICIES ==="
# Setup policies for fintech-group
cat << 'EOF' | vault policy write policy-fintech-group-admin -
path "secret/data/fintech-group/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "secret/metadata/fintech-group/*" {
  capabilities = ["list", "read", "delete"]
}
EOF

cat << 'EOF' | vault policy write policy-fintech-group-billing-service-rw -
path "secret/data/fintech-group/billing-service" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "secret/metadata/fintech-group/billing-service" {
  capabilities = ["read", "list"]
}
EOF

cat << 'EOF' | vault policy write policy-fintech-group-billing-service-ro -
path "secret/data/fintech-group/billing-service" {
  capabilities = ["read"]
}
path "secret/metadata/fintech-group/billing-service" {
  capabilities = ["read", "list"]
}
EOF

# Setup AppRole for billing-service
vault write auth/approle/role/role-fintech-group-billing-service \\
    token_policies="policy-fintech-group-billing-service-rw" \\
    token_ttl="24h"

ROLE_ID=$(vault read -format=json auth/approle/role/role-fintech-group-billing-service/role-id | jq -r '.data.role_id')
SECRET_ID=$(vault write -f -format=json auth/approle/role/role-fintech-group-billing-service/secret-id | jq -r '.data.secret_id')

echo "Demo setup complete!"
echo "Sample Role ID: $ROLE_ID"
echo "Sample Secret ID: $SECRET_ID"
"""

if __name__ == '__main__':
    print(run_ssh("192.168.86.128", "sarvar", "1", f"sudo -S bash -c '{seed_script}'"))
