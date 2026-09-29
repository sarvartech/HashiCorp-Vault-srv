import paramiko

def check_services(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    cmd = f"""
echo {password} | sudo -S systemctl is-enabled vault
sudo systemctl is-enabled vault-auto-unseal
sudo ufw status verbose
"""
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(check_services("192.168.86.128", "sarvar", "1"))
