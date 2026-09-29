import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def test_direct(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    cmd = """python3 -c '
import sys
sys.path.insert(0, "/usr/local/bin")
import vault_panel as vp

print("=== 1. PRODUCTION DOCTOR ===")
vp.production_doctor()

print("\n=== 2. BACKUP TEST ===")
vp.backup_vault_secrets()

print("\n=== 3. AUDIT LOG TEST ===")
vp.view_audit_logs()
'"""
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(test_direct("192.168.86.128", "sarvar", "1"))
