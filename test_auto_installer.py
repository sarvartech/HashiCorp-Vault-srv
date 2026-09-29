import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def test_installer_on_server(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)
    
    sftp = client.open_sftp()
    sftp.put("c:/Users/user/Documents/vault-srv/setup_vault_production.sh", "/tmp/setup_vault_production.sh")
    sftp.put("c:/Users/user/Documents/vault-srv/vault_panel.py", "/tmp/vault_panel.py")
    sftp.chmod("/tmp/setup_vault_production.sh", 0o755)
    sftp.close()
    
    cmd = f"echo {password} | sudo -S bash /tmp/setup_vault_production.sh"
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(test_installer_on_server("192.168.86.128", "sarvar", "1"))
