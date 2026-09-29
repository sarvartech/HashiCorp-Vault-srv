import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def run_ssh_stream(host, user, password, script_text):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {host}...")
    client.connect(host, username=user, password=password, timeout=20)
    
    sftp = client.open_sftp()
    remote_path = "/tmp/init_vault.sh"
    with sftp.file(remote_path, "w") as f:
        f.write(script_text)
    sftp.chmod(remote_path, 0o755)
    sftp.close()
    
    cmd = f"echo {password} | sudo -S bash {remote_path}"
    print("Executing init script...")
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    client.close()

init_script = """#!/bin/bash
set -e
export VAULT_ADDR="http://127.0.0.1:8200"

echo "=== 1. CHECK VAULT STATUS ==="
INIT_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.initialized' || echo "false")
echo "Initialized: $INIT_STATUS"

if [ "$INIT_STATUS" != "true" ]; then
    echo "=== 2. INITIALIZING VAULT ==="
    vault operator init -key-shares=3 -key-threshold=2 -format=json > /etc/vault.d/vault_init.json
    chmod 600 /etc/vault.d/vault_init.json
    echo "Vault initialized successfully!"
else
    echo "Vault is already initialized."
fi

KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json)
KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json)
ROOT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json)

echo "=== 3. UNSEALING VAULT ==="
vault operator unseal "$KEY1" > /dev/null
vault operator unseal "$KEY2" > /dev/null

export VAULT_TOKEN="$ROOT_TOKEN"
vault status

echo "=== 4. CREATE AUTO-UNSEAL SERVICE ==="
cat << 'EOF' > /usr/local/bin/vault-auto-unseal.sh
#!/bin/bash
export VAULT_ADDR="http://127.0.0.1:8200"
for i in {1..15}; do
    if curl -s http://127.0.0.1:8200/v1/sys/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if [ -f /etc/vault.d/vault_init.json ]; then
    SEALED=$(vault status -format=json 2>/dev/null | jq -r '.sealed' || echo "true")
    if [ "$SEALED" == "true" ]; then
        KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json)
        KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json)
        vault operator unseal "$KEY1" > /dev/null 2>&1
        vault operator unseal "$KEY2" > /dev/null 2>&1
        echo "Vault auto-unsealed successfully."
    fi
fi
EOF
chmod +x /usr/local/bin/vault-auto-unseal.sh

cat << 'EOF' > /etc/systemd/system/vault-auto-unseal.service
[Unit]
Description=Auto Unseal HashiCorp Vault
After=vault.service
Wants=vault.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vault-auto-unseal.sh
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vault-auto-unseal.service

echo "=== 5. CONFIGURE ENVIRONMENT & SECRETS ENGINE ==="
grep -qxF 'export VAULT_ADDR="http://127.0.0.1:8200"' /etc/profile || echo 'export VAULT_ADDR="http://127.0.0.1:8200"' >> /etc/profile
grep -qxF 'export VAULT_ADDR="http://127.0.0.1:8200"' /home/sarvar/.bashrc || echo 'export VAULT_ADDR="http://127.0.0.1:8200"' >> /home/sarvar/.bashrc
grep -qxF "export VAULT_TOKEN=\\"$ROOT_TOKEN\\"" /home/sarvar/.bashrc || echo "export VAULT_TOKEN=\\"$ROOT_TOKEN\\"" >> /home/sarvar/.bashrc

# Save credentials file for sarvar
cat << EOF > /home/sarvar/vault_credentials.txt
==================================================
           HASHICORP VAULT CREDENTIALS
==================================================
Vault Server URL (Local):  http://127.0.0.1:8200
Vault Server URL (Web UI): http://192.168.86.128:8200/ui

Root Token:
$ROOT_TOKEN

Unseal Key 1:
$KEY1

Unseal Key 2:
$KEY2

Unseal Key 3:
$(jq -r '.unseal_keys_b64[2]' /etc/vault.d/vault_init.json)

CLI Management Panel:
sudo vault-panel  (yoki 'vault-panel')
==================================================
EOF
chmod 600 /home/sarvar/vault_credentials.txt
chown sarvar:sarvar /home/sarvar/vault_credentials.txt

# Enable KV v2 secret engine if not exists
if ! vault secrets list -format=json | jq -e '."secret/"' > /dev/null 2>&1; then
    echo "Enabling KV-v2 engine at secret/..."
    vault secrets enable -path=secret kv-v2
else
    echo "KV-v2 engine already enabled at secret/."
fi

# Enable AppRole auth
if ! vault auth list -format=json | jq -e '."approle/"' > /dev/null 2>&1; then
    echo "Enabling AppRole auth..."
    vault auth enable approle
fi

# Enable Userpass auth
if ! vault auth list -format=json | jq -e '."userpass/"' > /dev/null 2>&1; then
    echo "Enabling Userpass auth..."
    vault auth enable userpass
fi

echo "=== 6. CONFIGURE FIREWALL (UFW) ==="
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 8200/tcp comment 'Vault UI and API'
ufw --force enable
ufw status verbose

echo "=== SETUP COMPLETE ==="
"""

if __name__ == '__main__':
    run_ssh_stream("192.168.86.128", "sarvar", "1", init_script)
