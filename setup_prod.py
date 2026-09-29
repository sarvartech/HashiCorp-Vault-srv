import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def setup_production_env(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    script = """#!/bin/bash
set -e
# 1. Passwordless sudo for administrator sarvar
echo "sarvar ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/sarvar
chmod 440 /etc/sudoers.d/sarvar

# 2. Vault audit directory and log file
mkdir -p /var/log/vault
chown -R vault:vault /var/log/vault
chmod 750 /var/log/vault

# 3. Enable Vault Audit Device
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json)

if ! vault audit list -format=json | jq -e '."file/"' > /dev/null 2>&1; then
    vault audit enable file file_path=/var/log/vault/vault_audit.log
    echo "Audit logging enabled at /var/log/vault/vault_audit.log"
else
    echo "Audit logging already enabled."
fi

# 4. Auto-launch banner and launcher on SSH login for sarvar
cat << 'EOF' > /etc/profile.d/00-vault-welcome.sh
# Production Vault Welcome & Auto Launch
if [ -n "$PS1" ] && [ "$USER" = "sarvar" ] && [ -z "$VAULT_PANEL_LAUNCHED" ]; then
    export VAULT_ADDR="http://127.0.0.1:8200"
    if [ -f /etc/vault.d/vault_init.json ]; then
        export VAULT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json 2>/dev/null)
    fi
    echo ""
    echo -e "\033[1;36m======================================================================\033[0m"
    echo -e "\033[1;32m      🔐 HASHICORP VAULT ENTERPRISE - PRODUCTION BOSHQARUV\033[0m"
    echo -e "      Web UI: \033[1;34mhttp://192.168.86.128:8200/ui\033[0m"
    echo -e "      Panelni ishga tushirish: \033[1;33mvault-panel\033[0m"
    echo -e "\033[1;36m======================================================================\033[0m"
fi
EOF

chmod +x /etc/profile.d/00-vault-welcome.sh
"""
    stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S bash -c '{script}'", get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(setup_production_env("192.168.86.128", "sarvar", "1"))
