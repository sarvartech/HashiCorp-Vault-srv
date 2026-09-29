import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def fix_env_and_unseal(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    script = """#!/bin/bash
set -e
# Ensure /etc/environment has VAULT_ADDR
grep -qxF 'VAULT_ADDR="http://127.0.0.1:8200"' /etc/environment || echo 'VAULT_ADDR="http://127.0.0.1:8200"' >> /etc/environment

# Also in /etc/profile.d/vault.sh
cat << 'EOF' > /etc/profile.d/vault.sh
export VAULT_ADDR="http://127.0.0.1:8200"
if [ -f /etc/vault.d/vault_init.json ]; then
    export VAULT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json 2>/dev/null)
fi
EOF

# Update vault-auto-unseal.sh
cat << 'EOF' > /usr/local/bin/vault-auto-unseal.sh
#!/bin/bash
export VAULT_ADDR="http://127.0.0.1:8200"

for i in {1..20}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8200/v1/sys/health || echo "000")
    if [ "$STATUS" == "200" ]; then
        echo "Vault already unsealed."
        exit 0
    elif [ "$STATUS" == "503" ]; then
        break
    fi
    sleep 1
done

if [ -f /etc/vault.d/vault_init.json ]; then
    KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json)
    KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json)
    vault operator unseal "$KEY1" > /dev/null 2>&1
    vault operator unseal "$KEY2" > /dev/null 2>&1
    echo "Vault auto-unsealed successfully."
fi
EOF
chmod +x /usr/local/bin/vault-auto-unseal.sh

# Restart vault service and test unseal
systemctl restart vault
sleep 2
/usr/local/bin/vault-auto-unseal.sh
export VAULT_ADDR="http://127.0.0.1:8200"
vault status | grep Sealed
"""
    sftp = client.open_sftp()
    with sftp.file("/tmp/fix_env.sh", "w") as f:
        f.write(script)
    sftp.chmod("/tmp/fix_env.sh", 0o755)
    sftp.close()

    cmd = f"echo {password} | sudo -S bash /tmp/fix_env.sh"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(fix_env_and_unseal("192.168.86.128", "sarvar", "1"))
