import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def test_panel_execution(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    # We simulate sending "1\n\n0\n" (Option 1: Tree View, Enter, Option 0: Exit)
    stdin, stdout, stderr = client.exec_command("vault-panel", get_pty=True)
    stdin.write("1\n\n0\n")
    stdin.flush()
    
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(test_panel_execution("192.168.86.128", "sarvar", "1"))
