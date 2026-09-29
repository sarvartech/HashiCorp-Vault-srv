import paramiko
import time

def run_ssh_stream(host, user, password, script_text):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {host}...")
    client.connect(host, username=user, password=password, timeout=20)
    
    # Write remote script
    sftp = client.open_sftp()
    remote_path = "/tmp/install_vault.sh"
    with sftp.file(remote_path, "w") as f:
        f.write(script_text)
    sftp.chmod(remote_path, 0o755)
    sftp.close()
    
    cmd = f"echo {password} | sudo -S bash {remote_path}"
    print("Executing script...")
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    client.close()

install_script = """#!/bin/bash
set -e

echo "=== 1. PACKAGES UPDATE & DEPENDENCIES ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl wget gpg lsb-release jq ufw python3 python3-pip

echo "=== 2. HASHICORP REPO ADD ==="
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg --yes
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list

apt-get update -y
apt-get install -y vault

echo "=== 3. VAULT CONFIGURATION ==="
mkdir -p /opt/vault/data
chown -R vault:vault /opt/vault

cat <<'EOF' > /etc/vault.d/vault.hcl
ui = true
disable_mlock = true

storage "file" {
  path = "/opt/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr = "http://192.168.86.128:8200"
cluster_addr = "http://192.168.86.128:8201"
EOF

chown -R vault:vault /etc/vault.d

echo "=== 4. SYSTEMD SERVICE ENABLE & RESTART ==="
systemctl daemon-reload
systemctl enable vault
systemctl restart vault
sleep 3

systemctl is-active vault || (echo "Vault service failed to start" && exit 1)
echo "Vault service is running successfully!"
"""

if __name__ == '__main__':
    run_ssh_stream("192.168.86.128", "sarvar", "1", install_script)
