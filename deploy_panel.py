import paramiko

def deploy_panel(host, user, password, local_file):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {host}...")
    client.connect(host, username=user, password=password, timeout=15)
    
    # SFTP upload
    sftp = client.open_sftp()
    remote_py = "/tmp/vault-panel.py"
    with open(local_file, "rb") as f:
        sftp.putfo(f, remote_py)
    sftp.close()
    
    # Move to /usr/local/bin and create wrapper
    commands = f"""
echo {password} | sudo -S mv /tmp/vault-panel.py /usr/local/bin/vault-panel.py
sudo chmod +x /usr/local/bin/vault-panel.py

cat << 'EOF' | sudo tee /usr/local/bin/vault-panel > /dev/null
#!/bin/bash
exec python3 /usr/local/bin/vault-panel.py "$@"
EOF

sudo chmod +x /usr/local/bin/vault-panel
echo "vault-panel installed successfully to /usr/local/bin/vault-panel"
"""
    stdin, stdout, stderr = client.exec_command(commands, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    print(out)
    client.close()

if __name__ == '__main__':
    deploy_panel("192.168.86.128", "sarvar", "1", "vault_panel.py")
