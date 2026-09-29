#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy Vault Enterprise Web Management Console to Linux Server
Sets up /opt/vault-web and creates systemd service vault-web-panel.service.
"""

import os
import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def deploy_web_panel(host, user, password, port=5000):
    print(f"\n=======================================================")
    print(f"🚀 {host} SERVERIGA VAULT WEB PANEL O'RNATILMOQDA...")
    print(f"=======================================================")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password, timeout=20)
    except Exception as e:
        print(f"❌ Ulanishda xatolik: {e}")
        return False

    sftp = client.open_sftp()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Create remote dirs
    stdin, stdout, stderr = client.exec_command("sudo mkdir -p /opt/vault-web/web/css /opt/vault-web/web/js && sudo chown -R sarvar:sarvar /opt/vault-web 2>/dev/null || true")
    stdout.read()

    print("📤 Fayllar serverga yuklanmoqda...")
    # Upload web_server.py
    sftp.put(os.path.join(base_dir, "web_server.py"), "/opt/vault-web/web_server.py")
    
    # Upload web files
    sftp.put(os.path.join(base_dir, "web", "index.html"), "/opt/vault-web/web/index.html")
    sftp.put(os.path.join(base_dir, "web", "css", "style.css"), "/opt/vault-web/web/css/style.css")
    sftp.put(os.path.join(base_dir, "web", "js", "app.js"), "/opt/vault-web/web/js/app.js")
    sftp.close()

    # Remote systemd service setup
    remote_script = f"""#!/bin/bash
set -e

# Systemd unit file
cat << 'EOF' > /etc/systemd/system/vault-web-panel.service
[Unit]
Description=HashiCorp Vault Enterprise Web Console
After=network.target vault.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vault-web
ExecStart=/usr/bin/python3 /opt/vault-web/web_server.py {port}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vault-web-panel.service
systemctl restart vault-web-panel.service

# Firewall port 5000
ufw allow {port}/tcp comment 'Vault Web Console' > /dev/null 2>&1 || true

# Nginx subpath /app/ integration if nginx exists
if [ -f /etc/nginx/sites-available/vault ]; then
    if ! grep -q 'location /app/' /etc/nginx/sites-available/vault; then
        sed -i '/location \/ {{/i \    location /app/ {{\\n        proxy_pass http://127.0.0.1:{port}/;\\n        proxy_set_header Host $host;\\n        proxy_set_header X-Real-IP $remote_addr;\\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\\n        proxy_set_header X-Forwarded-Proto $scheme;\\n    }}\\n' /etc/nginx/sites-available/vault
        nginx -t && systemctl reload nginx
    fi
fi

echo "✔ Web Panel xizmati muvaffaqiyatli yoqildi!"
"""
    cmd = f"echo {password} | sudo -S bash -c '{remote_script}'"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")

    client.close()
    print(f"\n=======================================================")
    print(f"✔ VAULT WEB PANEL TAYYOR!")
    print(f"  To'g'ridan-to'g'ri Port: http://{host}:{port}")
    print(f"  Domen orqali:          https://vault-srv.trustbank.uz/app/")
    print(f"=======================================================\n")
    return True

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.86.128"
    user = sys.argv[2] if len(sys.argv) > 2 else "sarvar"
    pwd = sys.argv[3] if len(sys.argv) > 3 else "1"
    deploy_web_panel(host, user, pwd)
