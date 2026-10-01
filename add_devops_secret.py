import json
import paramiko

SERVER_IP = "192.168.86.70"
USERNAME = "sarvar"
PASSWORD = "1"

def main():
    with open("vault_credentials.json") as f:
        creds = json.load(f)
    token = creds["root_token"]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_IP, username=USERNAME, password=PASSWORD, timeout=10)

    # Remote commands
    remote_script = f"""#!/bin/bash
set -e
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"
export VAULT_TOKEN="{token}"

# 1. Store secret in Vault
vault kv put secret/apps/devops-app api_token="dsfdsfdfd1f2d5ds5g5j8uk5dsc2s2ds2d"

# 2. Create specific policy for this secret only
cat << 'EOF' > /tmp/devops_app_policy.hcl
path "secret/data/apps/devops-app" {{
  capabilities = ["read"]
}}
path "secret/metadata/apps/devops-app" {{
  capabilities = ["list", "read"]
}}
EOF
vault policy write devops-app-policy /tmp/devops_app_policy.hcl
rm -f /tmp/devops_app_policy.hcl

# 3. Create dedicated AppRole for DevOps application
vault write auth/approle/role/devops-app-role \\
    secret_id_ttl=720h \\
    token_ttl=24h \\
    token_policies="devops-app-policy"

ROLE_ID=$(vault read -format=json auth/approle/role/devops-app-role/role-id | jq -r .data.role_id)
SECRET_ID=$(vault write -f -format=json auth/approle/role/devops-app-role/secret-id | jq -r .data.secret_id)

# 4. Standalone token (for immediate use or testing)
STANDALONE_TOKEN=$(vault token create -policy="devops-app-policy" -ttl="720h" -format=json | jq -r .auth.client_token)

# 5. Userpass account for DevOps engineer (optional, for web UI access)
vault write auth/userpass/users/devops_engineer \\
    password="DevOpsSecurePassword2026!" \\
    policies="devops-app-policy"

echo "RESULT_JSON:{{\\"role_id\\": \\"$ROLE_ID\\", \\"secret_id\\": \\"$SECRET_ID\\", \\"standalone_token\\": \\"$STANDALONE_TOKEN\\"}}"
"""
    sftp = client.open_sftp()
    with sftp.open("/tmp/add_devops_secret.sh", "w") as f:
        f.write(remote_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S bash /tmp/add_devops_secret.sh")
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    client.close()

    print("Command Output:\n", out)
    if "RESULT_JSON:" in out:
        result_str = out.split("RESULT_JSON:")[1].strip()
        data = json.loads(result_str)
        with open("devops_access_info.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Successfully saved to devops_access_info.json!")

if __name__ == "__main__":
    main()
