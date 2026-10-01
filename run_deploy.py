import os
import sys
import json
import paramiko

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SERVER_IP = "192.168.86.70"
USERNAME = "sarvar"
PASSWORD = "1"

def main():
    print(f"Connecting to {SERVER_IP}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_IP, username=USERNAME, password=PASSWORD, timeout=15)
    
    # SFTP upload setup script
    print("Uploading setup_remote_vault.sh to /tmp/setup_remote_vault.sh...")
    sftp = client.open_sftp()
    
    # Convert CRLF to LF just in case
    with open("setup_remote_vault.sh", "r", encoding="utf-8") as f:
        content = f.read().replace("\r\n", "\n")
    
    with sftp.open("/tmp/setup_remote_vault.sh", "w") as remote_f:
        remote_f.write(content)
    sftp.close()
    
    # Run the script with sudo
    print("Executing setup script on remote server...")
    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S bash /tmp/setup_remote_vault.sh")
    
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line, end="")
        
    err = stderr.read().decode('utf-8', errors='replace')
    err_filtered = "\n".join([l for l in err.splitlines() if not l.startswith("[sudo] password for")])
    if err_filtered.strip():
        print(f"\n[STDERR INFO]:\n{err_filtered}")
        
    exit_status = stdout.channel.recv_exit_status()
    print(f"\nExit status: {exit_status}")
    if exit_status != 0:
        raise RuntimeError(f"Script failed with exit status {exit_status}")
        
    # Download credentials and CA certificate
    print("\nRetrieving credentials and CA certificate...")
    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S cat /root/vault_credentials.json")
    creds_raw = stdout.read().decode('utf-8')
    with open("vault_credentials.json", "w", encoding="utf-8") as f:
        f.write(creds_raw)
    print("Saved vault_credentials.json locally.")

    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S cat /opt/vault/tls/ca.crt")
    ca_raw = stdout.read().decode('utf-8')
    with open("vault_ca.crt", "w", encoding="utf-8") as f:
        f.write(ca_raw)
    print("Saved vault_ca.crt locally.")

    # Retrieve AppRole role-id and secret-id for demonstration
    root_token = json.loads(creds_raw).get("root_token")
    cmd_approle = f"""
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_CACERT="/opt/vault/tls/ca.crt"
export VAULT_TOKEN="{root_token}"
ROLE_ID=$(vault read -format=json auth/approle/role/backend-service/role-id | jq -r .data.role_id)
SECRET_ID=$(vault write -f -format=json auth/approle/role/backend-service/secret-id | jq -r .data.secret_id)
echo "{{\\"role_id\\": \\"$ROLE_ID\\", \\"secret_id\\": \\"$SECRET_ID\\"}}"
"""
    stdin, stdout, stderr = client.exec_command(f"echo {PASSWORD} | sudo -S bash -c '{cmd_approle}'")
    approle_info = stdout.read().decode('utf-8').strip()
    with open("approle_credentials.json", "w", encoding="utf-8") as f:
        f.write(approle_info)
    print("Saved approle_credentials.json locally.")

    client.close()
    print("\n=== ALL COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()
