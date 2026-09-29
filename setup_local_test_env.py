#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup full local test environment on 192.168.86.128:
1. Reinstall Vault with domain https://vault-srv.trustbank.uz
2. Install & Configure Nginx SSL Reverse Proxy (443 -> 8200)
3. Generate SSL certificate for vault-srv.trustbank.uz
4. Seed sample secret (secret/data/humo/1-token) with AppRole
5. Test everything locally on the server
"""

import paramiko
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HOST = "192.168.86.128"
USER = "sarvar"
PASS = "1"
DOMAIN = "vault-srv.trustbank.uz"

def run():
    print(f"🚀 {HOST} serveriga ulanish...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS, timeout=20)
    
    sftp = client.open_sftp()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("📤 Skriptlarni serverga yuklash...")
    for f in ["reinstall_vault.py", "vault_panel.py"]:
        local_p = os.path.join(script_dir, f)
        if os.path.exists(local_p):
            sftp.put(local_p, f"/tmp/{f}")
            sftp.chmod(f"/tmp/{f}", 0o755)
            
    # Setup script on remote
    remote_setup = """#!/bin/bash
set -e

echo "=== 1. VAULTNI QAYTA O'RNATISH (DOMAIN BILAN) ==="
python3 /tmp/reinstall_vault.py --domain "https://vault-srv.trustbank.uz" --proxy-cidr "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16" -y

echo "=== 2. NGINX VA OPENSSL O'RNATISH ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y > /dev/null
apt-get install -y nginx openssl > /dev/null

echo "=== 3. SSL SERTIFIKAT YARATISH (vault-srv.trustbank.uz) ==="
mkdir -p /etc/ssl/certs /etc/ssl/private
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/vault.key \
  -out /etc/ssl/certs/vault.crt \
  -subj "/CN=vault-srv.trustbank.uz/O=Trustbank/C=UZ" \
  -addext "subjectAltName=DNS:vault-srv.trustbank.uz,IP:192.168.86.128,IP:127.0.0.1"

echo "=== 4. NGINX REVERSE PROXY KONFIGURATSIYASI ==="
cat << 'EOF' > /etc/nginx/sites-available/vault
server {
    listen 80;
    server_name vault-srv.trustbank.uz;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl default_server;
    server_name vault-srv.trustbank.uz;

    ssl_certificate     /etc/ssl/certs/vault.crt;
    ssl_certificate_key /etc/ssl/private/vault.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/vault /etc/nginx/sites-enabled/vault
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "=== 5. FIREWALL (UFW) SOZLASH ==="
ufw allow 80/tcp comment 'HTTP Proxy' > /dev/null 2>&1 || true
ufw allow 443/tcp comment 'HTTPS Proxy' > /dev/null 2>&1 || true
ufw allow 8200/tcp comment 'Vault Direct' > /dev/null 2>&1 || true

echo "=== 6. DEMO MA'LUMOT (humo/1-token) SEED QILISH ==="
ROOT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json)
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="$ROOT_TOKEN"

# Policy yaratish
vault policy write policy-humo-rw - << 'POL'
path "secret/data/humo/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "secret/metadata/humo/*" {
  capabilities = ["read", "list"]
}
POL

# Secret yozish
vault kv put secret/humo/1-token token="tok_humo_live_98838271" merchant_id="HUMO_TB_01" terminal="TB00123"

# AppRole yaratish (aniq role_id va secret_id bilan)
vault write auth/approle/role/role-humo-1-token \
    token_policies="policy-humo-rw" \
    token_ttl="720h" \
    token_max_ttl="720h"

vault write auth/approle/role/role-humo-1-token/role-id role_id="8df244fc-57e8-9eac-10d2-bad18961fa35"
vault write auth/approle/role/role-humo-1-token/custom-secret-id secret_id="2c9da07d-0103-dbb1-ad04-a7c3bba783cd"

echo "=== 7. MAHALLIY TEST TEKSHIRUVI (HTTPS PROXY ORQALI) ==="
# Ichki hosts ga ham yozib qo'yamiz
grep -q "vault-srv.trustbank.uz" /etc/hosts || echo "127.0.0.1 vault-srv.trustbank.uz" >> /etc/hosts
curl -k -s https://vault-srv.trustbank.uz/v1/sys/health | jq .

echo ""
echo "✔ BARChASI TAYYOR! ROOT TOKEN: $ROOT_TOKEN"
"""
    
    import io
    sftp.putfo(io.BytesIO(remote_setup.encode('utf-8')), "/tmp/run_setup_env.sh")
    sftp.chmod("/tmp/run_setup_env.sh", 0o755)
    sftp.close()
    
    print("⚙️ Serverda o'rnatish jarayoni boshlandi...")
    cmd = f"echo {PASS} | sudo -S bash /tmp/run_setup_env.sh"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    client.close()
    print("\n🎉 O'rnatish va Nginx SSL sozlash to'liq yakunlandi!")

if __name__ == '__main__':
    run()
