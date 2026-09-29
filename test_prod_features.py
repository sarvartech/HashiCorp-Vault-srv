import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def test_production_features(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    # Send "14\n\n12\n\n0\n" (Production doctor, Enter, Backup, Enter, Exit)
    stdin, stdout, stderr = client.exec_command("vault-panel", get_pty=True)
    stdin.write("14\n\n12\n\n0\n")
    stdin.flush()
    
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(test_production_features("192.168.86.128", "sarvar", "1"))
