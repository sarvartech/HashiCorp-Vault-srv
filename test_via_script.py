import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def test_via_script(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    
    script = """#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/bin')
import importlib.util
spec = importlib.util.spec_from_file_location("vp", "/usr/local/bin/vault-panel.py")
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)

print("=== 1. PRODUCTION DOCTOR ===")
vp.production_doctor()

print("\\n=== 2. BACKUP TEST ===")
vp.backup_vault_secrets()

print("\\n=== 3. AUDIT LOG TEST ===")
vp.view_audit_logs()
"""
    sftp = client.open_sftp()
    with sftp.file("/tmp/test_runner.py", "w") as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/test_runner.py", get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    print(test_via_script("192.168.86.128", "sarvar", "1"))
