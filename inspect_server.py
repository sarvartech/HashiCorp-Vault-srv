import paramiko

def run_ssh(host, user, password, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    if "sudo" in cmd:
        stdin.write(password + "\n")
        stdin.flush()
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    commands = """
echo "=== INTERNET CHECK ==="
curl -I -s --connect-timeout 5 https://www.google.com | head -n 2
echo "=== UFW STATUS ==="
sudo -S ufw status verbose
echo "=== VAULT CHECK ==="
which vault || echo "vault not found"
echo "=== LISTENING PORTS ==="
ss -tulpn | grep -E '8200|22'
"""
    print(run_ssh("192.168.86.128", "sarvar", "1", commands))
