import paramiko
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')

def test_restart_and_unseal(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    cmd = f"""
echo {password} | sudo -S systemctl restart vault
sleep 2
echo "Vault status after restart:"
vault status | grep Sealed || true
echo "Running auto-unseal service:"
sudo systemctl start vault-auto-unseal.service
sleep 2
vault status | grep Sealed || true
"""
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(test_restart_and_unseal("192.168.86.128", "sarvar", "1"))
