import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def test_login_flow(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    # We simulate:
    # 1. Enter for default Vault URL (http://127.0.0.1:8200)
    # 2. Enter our actual root token "YOUR_VAULT_ROOT_TOKEN"
    # 3. Enter to go to main menu
    # 4. "0" to exit
    import os
    token = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")
    stdin, stdout, stderr = client.exec_command("vault-panel", get_pty=True)
    stdin.write(f"\n{token}\n\n0\n")
    stdin.flush()
    
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(test_login_flow("192.168.86.128", "sarvar", "1"))
