import paramiko
import sys

# Ensure UTF-8 output handling on Windows
sys.stdout.reconfigure(encoding='utf-8')

def run_ssh(host, user, password, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    if "sudo" in cmd:
        stdin.write(password + "\n")
        stdin.flush()
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    commands = """
echo "=== VAULT VERSION ==="
vault version || echo "no vault"
echo "=== SYSTEMCTL STATUS VAULT ==="
sudo -S systemctl status vault --no-pager
echo "=== PORT CHECK ==="
ss -tulpn | grep 8200 || echo "port 8200 not listening yet"
"""
    print(run_ssh("192.168.86.128", "sarvar", "1", commands))
