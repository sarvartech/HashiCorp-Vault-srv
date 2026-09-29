import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def fix_perms_and_audit(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    script = """#!/bin/bash
set -e
# 1. Backups directory in sarvar home & /var/backups/vault
mkdir -p /home/sarvar/vault_backups /var/backups/vault
chown -R sarvar:sarvar /home/sarvar/vault_backups /var/backups/vault
chmod 755 /home/sarvar/vault_backups /var/backups/vault

# 2. Audit log file
touch /var/log/vault/vault_audit.log
chown vault:vault /var/log/vault/vault_audit.log
chmod 644 /var/log/vault/vault_audit.log

# Add sarvar to vault group
usermod -aG vault sarvar || true

# Test reading vault status to generate an audit log entry
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json)
vault kv list secret/ > /dev/null 2>&1 || true

ls -lh /var/log/vault/vault_audit.log
"""
    stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S bash -c '{script}'", get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(fix_perms_and_audit("192.168.86.128", "sarvar", "1"))
