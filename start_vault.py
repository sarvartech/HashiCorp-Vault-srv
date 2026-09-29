import paramiko
import sys
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
echo "=== CAT VAULT.HCL ==="
sudo -S cat /etc/vault.d/vault.hcl
echo "=== START VAULT ==="
sudo systemctl start vault
sleep 2
echo "=== SYSTEMCTL STATUS ==="
sudo systemctl status vault --no-pager
echo "=== JOURNALCTL ==="
sudo journalctl -u vault -n 25 --no-pager
"""
    print(run_ssh("192.168.86.128", "sarvar", "1", commands))
