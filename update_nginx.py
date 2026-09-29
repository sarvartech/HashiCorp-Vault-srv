import paramiko

conf = """server {
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

    location /app/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

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
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("192.168.86.128", username="sarvar", password="1", timeout=10)

sftp = client.open_sftp()
with sftp.file("/tmp/vault_nginx.conf", "w") as f:
    f.write(conf)
sftp.close()

stdin, stdout, stderr = client.exec_command("echo 1 | sudo -S cp /tmp/vault_nginx.conf /etc/nginx/sites-available/vault && echo 1 | sudo -S nginx -t && echo 1 | sudo -S systemctl reload nginx")
print(stdout.read().decode('utf-8'))
client.close()
