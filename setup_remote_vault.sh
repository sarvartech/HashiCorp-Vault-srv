#!/bin/bash
set -e

echo "=== 1. Setting up directories ==="
mkdir -p /opt/vault/data /opt/vault/tls /var/log/vault /etc/vault.d
chown -R vault:vault /opt/vault /var/log/vault /etc/vault.d
chmod 700 /opt/vault/data /opt/vault/tls

echo "=== 2. Creating TLS Certificates ==="
cd /opt/vault/tls

# 1. Root CA Key and Certificate
if [ ! -f ca.key ]; then
    openssl genrsa -out ca.key 4096
    openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/C=UZ/ST=Tashkent/O=Vault-Security/CN=Vault-Internal-Root-CA"
fi

# 2. Server Key and CSR with SAN
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

openssl req -new -key vault.key -out vault.csr -subj "/C=UZ/ST=Tashkent/O=Vault-Security/CN=192.168.86.70"
openssl x509 -req -in vault.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out vault.crt -days 1825 -extfile san.ext

chown vault:vault /opt/vault/tls/*
chmod 600 /opt/vault/tls/*.key
chmod 644 /opt/vault/tls/*.crt

# Trust CA in OS trust store
cp ca.crt /usr/local/share/ca-certificates/vault-ca.crt
update-ca-certificates

echo "=== 3. Writing /etc/vault.d/vault.hcl ==="
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

echo "=== 4. Setting environment variables ==="
cat << 'EOF' > /etc/profile.d/vault.sh
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"
EOF
chmod +x /etc/profile.d/vault.sh

echo "=== 5. Restarting Vault Service ==="
systemctl daemon-reload
systemctl enable vault
systemctl restart vault
sleep 3
systemctl status vault --no-pager

echo "=== 6. Initializing and Unsealing Vault ==="
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"

if ! vault status -format=json 2>/dev/null | grep -q '"initialized": true'; then
    echo "Initializing Vault with Shamir 3 shares, threshold 2..."
    vault operator init -key-shares=3 -key-threshold=2 -format=json > /root/vault_credentials.json
    chmod 600 /root/vault_credentials.json
fi

# Unseal Vault
K1=$(jq -r '.unseal_keys_b64[0]' /root/vault_credentials.json)
K2=$(jq -r '.unseal_keys_b64[1]' /root/vault_credentials.json)
ROOT_TOKEN=$(jq -r '.root_token' /root/vault_credentials.json)

vault operator unseal "$K1"
vault operator unseal "$K2"

export VAULT_TOKEN="$ROOT_TOKEN"
vault status

echo "=== 7. Configuring Audit Devices and Secret Engines ==="
# Audit log file (all accesses logged and secret values hashed)
mkdir -p /var/log/vault
chown vault:vault /var/log/vault
vault audit enable file file_path=/var/log/vault/vault_audit.log || true

# Secrets engine KV version 2
vault secrets enable -version=2 -path=secret kv || true

# Auth methods
vault auth enable approle || true
vault auth enable userpass || true

echo "=== 8. Creating Fine-Grained Least-Privilege Policies ==="
# 1. Dev team policy: only access dev path, strictly denied from prod
cat << 'PEOF' > /tmp/dev_policy.hcl
# Access strictly restricted to dev secrets
path "secret/data/dev/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "secret/metadata/dev/*" {
  capabilities = ["list", "read", "delete"]
}

# DevOps or Devs cannot see production secrets
path "secret/data/prod/*" {
  capabilities = ["deny"]
}
path "secret/metadata/prod/*" {
  capabilities = ["deny"]
}
PEOF
vault policy write dev-policy /tmp/dev_policy.hcl
rm -f /tmp/dev_policy.hcl

# 2. Production Read-only policy for automated app
cat << 'PEOF' > /tmp/prod_readonly.hcl
path "secret/data/prod/*" {
  capabilities = ["read"]
}
path "secret/metadata/prod/*" {
  capabilities = ["list", "read"]
}
PEOF
vault policy write prod-readonly /tmp/prod_readonly.hcl
rm -f /tmp/prod_readonly.hcl

echo "=== 9. Creating Users and AppRoles ==="
# Developer user (e.g. dev_user with password)
vault write auth/userpass/users/dev_user \
    password="DevUserPass2026!" \
    policies="dev-policy"

# AppRole for automated service
vault write auth/approle/role/backend-service \
    secret_id_ttl=720h \
    token_num_uses=0 \
    token_ttl=1h \
    token_max_ttl=4h \
    token_policies="prod-readonly"

echo "=== 10. Writing Sample Encrypted Secrets ==="
vault kv put secret/dev/database username="dev_admin" password="DevPasswordSecret123" host="192.168.86.70"
vault kv put secret/prod/database username="prod_secure_admin" password="ProdSuperEncryptedPassword999!" host="db.prod.internal"

echo "=== Setup complete! ==="
