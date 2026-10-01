import json
import paramiko

SERVER_IP = "192.168.86.70"
USERNAME = "sarvar"
PASSWORD = "1"

def main():
    print("=== Configuring mTLS (Client Certificate) Authentication in Vault ===")
    with open("vault_credentials.json") as f:
        creds = json.load(f)
    root_token = creds["root_token"]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_IP, username=USERNAME, password=PASSWORD, timeout=10)

    remote_script = f"""#!/bin/bash
set -e

export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"
export VAULT_TOKEN="{root_token}"

echo "1. Generating Application Client Key & Certificate..."
cd /opt/vault/tls

# Generate client private key
openssl genrsa -out client_app.key 2048

# Generate CSR
openssl req -new -key client_app.key -out client_app.csr -subj "/C=UZ/ST=Tashkent/O=Production-App/CN=devops-app-service"

# Sign client certificate using our Vault CA
openssl x509 -req -in client_app.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client_app.crt -days 730

# Permissions
chmod 600 client_app.key
chmod 644 client_app.crt
chown vault:vault client_app.*

echo "2. Enabling TLS Cert Auth Method in Vault..."
vault auth enable cert || true

echo "3. Registering Client Certificate with devops-app-policy..."
vault write auth/cert/certs/devops-app \\
    display_name="devops-app-service" \\
    policies="devops-app-policy" \\
    certificate=@/opt/vault/tls/client_app.crt \\
    ttl=3600

echo "4. Testing mTLS login from server CLI..."
LOGIN_OUTPUT=$(curl -s --cacert /opt/vault/tls/ca.crt --cert /opt/vault/tls/client_app.crt --key /opt/vault/tls/client_app.key -X POST https://127.0.0.1:8200/v1/auth/cert/login)
echo "Login output: $LOGIN_OUTPUT"

echo "=== Cert Auth configured successfully! ==="
"""
    sftp = client.open_sftp()
    with sftp.open("/tmp/setup_cert_auth.sh", "w") as f:
        f.write(remote_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S bash /tmp/setup_cert_auth.sh")
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("Remote Output:\n", out)
    if err.strip():
        print("Remote Stderr:\n", err)

    # Download client certificate and private key to workspace
    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S cat /opt/vault/tls/client_app.crt")
    client_crt = stdout.read().decode('utf-8')
    with open("client_app.crt", "w", encoding="utf-8") as f:
        f.write(client_crt)
    print("Saved client_app.crt locally.")

    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S cat /opt/vault/tls/client_app.key")
    client_key = stdout.read().decode('utf-8')
    with open("client_app.key", "w", encoding="utf-8") as f:
        f.write(client_key)
    print("Saved client_app.key locally.")

    client.close()

if __name__ == "__main__":
    main()
