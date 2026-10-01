import sys
import time
import json
import paramiko

SERVER_IP = "192.168.86.70"
USERNAME = "sarvar"
PASSWORD = "1"

def run_sudo(client, command, ignore_error=False, timeout=120):
    print(f"\n[EXEC] {command[:100]}..." if len(command) > 100 else f"\n[EXEC] {command}")
    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S bash -c {repr(command)}", timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    exit_status = stdout.channel.recv_exit_status()
    
    # filter out sudo password prompt
    err_filtered = "\n".join([line for line in err.splitlines() if not line.startswith("[sudo] password for")])
    
    if exit_status != 0 and not ignore_error:
        print(f"[ERROR exit={exit_status}]\nStdout: {out}\nStderr: {err_filtered}")
        raise RuntimeError(f"Command failed with exit code {exit_status}: {command}")
    
    if out.strip():
        print(f"[OUT]\n{out.strip()}")
    if err_filtered.strip():
        print(f"[STDERR]\n{err_filtered.strip()}")
    return out

def main():
    print("=== Connecting to 192.168.86.70 ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_IP, username=USERNAME, password=PASSWORD, timeout=15)
    print("=== Connected successfully ===")

    # Step 1: Install prerequisites and HashiCorp repository
    print("\n--- 1. Installing Prerequisites and HashiCorp APT Repo ---")
    run_sudo(client, "apt-get update && apt-get install -y curl gpg lsb-release jq openssl")
    
    run_sudo(client, "wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg --yes")
    run_sudo(client, "echo \"deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main\" > /etc/apt/sources.list.d/hashicorp.list")
    run_sudo(client, "apt-get update && apt-get install -y vault")
    
    # Verify vault installation
    vault_version = run_sudo(client, "vault --version")
    print(f"Installed Vault: {vault_version.strip()}")

    # Step 2: Create directories
    print("\n--- 2. Setting up directories & permissions ---")
    run_sudo(client, "mkdir -p /opt/vault/data /opt/vault/tls /var/log/vault /etc/vault.d")
    run_sudo(client, "chown -R vault:vault /opt/vault /var/log/vault")
    run_sudo(client, "chmod 700 /opt/vault/data /opt/vault/tls")

    # Step 3: Generate TLS Certificates
    print("\n--- 3. Generating TLS Certificates (CA + Server Cert with SAN) ---")
    ssl_commands = """
set -e
cd /opt/vault/tls

# 1. Root CA Key and Certificate
if [ ! -f ca.key ]; then
    openssl genrsa -out ca.key 4096
    openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/C=UZ/ST=Tashkent/O=Vault-VRS/CN=Vault-Internal-Root-CA"
fi

# 2. Server Key and CSR
openssl genrsa -out vault.key 2048

cat << 'EOF' > san.ext
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
IP.1 = 192.168.86.70
IP.2 = 127.0.0.1
DNS.1 = netbox-srv
DNS.2 = vault.local
DNS.3 = localhost
EOF

openssl req -new -key vault.key -out vault.csr -subj "/C=UZ/ST=Tashkent/O=Vault-VRS/CN=192.168.86.70"
openssl x509 -req -in vault.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out vault.crt -days 1825 -extfile san.ext

# Permissions
chown vault:vault /opt/vault/tls/*
chmod 600 /opt/vault/tls/*.key
chmod 644 /opt/vault/tls/*.crt

# Trust CA locally on the server
cp ca.crt /usr/local/share/ca-certificates/vault-ca.crt
update-ca-certificates
"""
    run_sudo(client, ssl_commands)

    # Step 4: Vault Configuration
    print("\n--- 4. Writing /etc/vault.d/vault.hcl ---")
    vault_hcl = """
cat << 'EOF' > /etc/vault.d/vault.hcl
ui = true
disable_mlock = false

storage "raft" {
  path    = "/opt/vault/data"
  node_id = "vault-node-1"
}

listener "tcp" {
  address            = "0.0.0.0:8200"
  tls_cert_file      = "/opt/vault/tls/vault.crt"
  tls_key_file       = "/opt/vault/tls/vault.key"
  tls_client_ca_file = "/opt/vault/tls/ca.crt"
  tls_min_version    = "tls12"
}

api_addr     = "https://192.168.86.70:8200"
cluster_addr = "https://192.168.86.70:8201"
EOF

chown vault:vault /etc/vault.d/vault.hcl
chmod 640 /etc/vault.d/vault.hcl
"""
    run_sudo(client, vault_hcl)

    # Step 5: Setup Environment Variables
    print("\n--- 5. Configuring System Environment ---")
    env_commands = """
cat << 'EOF' > /etc/profile.d/vault.sh
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"
EOF
chmod +x /etc/profile.d/vault.sh
"""
    run_sudo(client, env_commands)

    # Step 6: Enable and Start Vault Service
    print("\n--- 6. Starting Vault Service ---")
    run_sudo(client, "systemctl daemon-reload")
    run_sudo(client, "systemctl enable vault")
    run_sudo(client, "systemctl restart vault")
    time.sleep(3)
    status = run_sudo(client, "systemctl status vault --no-pager")
    print(f"Vault service status:\n{status}")

    # Step 7: Check if Vault is initialized
    print("\n--- 7. Checking Vault Initialization ---")
    init_check = run_sudo(client, "export VAULT_ADDR='https://127.0.0.1:8200' && export VAULT_CACERT='/opt/vault/tls/ca.crt' && vault status -format=json", ignore_error=True)
    
    is_initialized = False
    try:
        status_data = json.loads(init_check)
        is_initialized = status_data.get("initialized", False)
    except Exception:
        pass

    creds = None
    if not is_initialized:
        print("\n--- Vault is NOT initialized. Initializing with Shamir's 3 keys, threshold 2 ---")
        init_out = run_sudo(client, "export VAULT_ADDR='https://127.0.0.1:8200' && export VAULT_CACERT='/opt/vault/tls/ca.crt' && vault operator init -key-shares=3 -key-threshold=2 -format=json")
        creds = json.loads(init_out)
        
        # Save credentials securely on server in /root/vault_credentials.json (mode 600)
        run_sudo(client, f"cat << 'EOF' > /root/vault_credentials.json\n{json.dumps(creds, indent=2)}\nEOF\nchmod 600 /root/vault_credentials.json")
        print("Vault credentials saved securely to /root/vault_credentials.json")
    else:
        print("\nVault is already initialized! Checking if credentials file exists on server...")
        try:
            creds_raw = run_sudo(client, "cat /root/vault_credentials.json", ignore_error=True)
            creds = json.loads(creds_raw)
        except Exception:
            print("Could not load /root/vault_credentials.json")

    # Step 8: Unseal Vault if sealed
    print("\n--- 8. Unsealing Vault ---")
    if creds and "unseal_keys_b64" in creds:
        k1 = creds["unseal_keys_b64"][0]
        k2 = creds["unseal_keys_b64"][1]
        run_sudo(client, f"export VAULT_ADDR='https://127.0.0.1:8200' && export VAULT_CACERT='/opt/vault/tls/ca.crt' && vault operator unseal {k1}")
        unseal2 = run_sudo(client, f"export VAULT_ADDR='https://127.0.0.1:8200' && export VAULT_CACERT='/opt/vault/tls/ca.crt' && vault operator unseal {k2}")
        print("Vault Unsealed successfully!")

    # Step 9: Configure Audit Log & KV engine & AppRole
    if creds and "root_token" in creds:
        root_token = creds["root_token"]
        print("\n--- 9. Configuring Audit Devices, KV Secrets Engine, and Auth Methods ---")
        post_config = """
export VAULT_ADDR='https://127.0.0.1:8200'
export VAULT_CACERT='/opt/vault/tls/ca.crt'
export VAULT_TOKEN='__ROOT_TOKEN__'

# 1. Enable audit log (all access logged and hashed)
vault audit enable file file_path=/var/log/vault/vault_audit.log || true

# 2. Enable KV version 2 secrets engine at secret/
vault secrets enable -version=2 kv || true

# 3. Enable AppRole auth method
vault auth enable approle || true

# 4. Enable Userpass auth method
vault auth enable userpass || true

# 5. Create policy for developers/apps (least-privilege)
cat << 'PEOF' > /tmp/developer_policy.hcl
# Developers can read/write their own team secrets
path "secret/data/dev/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "secret/metadata/dev/*" {
  capabilities = ["list", "read", "delete"]
}

# Sysadmin/DevOps cannot see production secrets without explicit policy
path "secret/data/prod/*" {
  capabilities = ["deny"]
}
PEOF

vault policy write dev-team /tmp/developer_policy.hcl
rm -f /tmp/developer_policy.hcl

# 6. Create production read-only policy for microservices
cat << 'PEOF' > /tmp/prod_readonly_policy.hcl
path "secret/data/prod/*" {
  capabilities = ["read"]
}
path "secret/metadata/prod/*" {
  capabilities = ["list", "read"]
}
PEOF

vault policy write prod-readonly /tmp/prod_readonly_policy.hcl
rm -f /tmp/prod_readonly_policy.hcl

# 7. Create AppRole for automated app/DevOps pipeline
vault write auth/approle/role/backend-service \\
    secret_id_ttl=720h \\
    token_num_uses=0 \\
    token_ttl=1h \\
    token_max_ttl=4h \\
    token_policies="prod-readonly"

# 8. Create a sample secret in dev and prod
vault kv put secret/dev/database username="dev_user" password="DevPassword123!" host="192.168.86.70"
vault kv put secret/prod/database username="prod_admin" password="SuperSecretProdPassword987!" host="db.production.local"
""".replace("__ROOT_TOKEN__", root_token)
        run_sudo(client, post_config)
        print("Engines, Audit log, Policies, and Sample Secrets configured successfully!")

    # Retrieve and save local copy of credentials and CA certificate
    print("\n--- 10. Pulling CA Certificate and Credentials locally ---")
    ca_cert = run_sudo(client, "cat /opt/vault/tls/ca.crt")
    with open("vault_ca.crt", "w", encoding="utf-8") as f:
        f.write(ca_cert)

    if creds:
        with open("vault_credentials.json", "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
        print("Credentials saved locally to vault_credentials.json")

    print("\n=== DEPLOYMENT COMPLETE ===")
    client.close()

if __name__ == "__main__":
    main()
