import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

def run_ssh(host, user, password, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    client.close()
    return out

if __name__ == '__main__':
    commands = """
python3 -c "import urllib.request, json; print('Standard library OK')"
python3 -c "import requests; print('requests OK')" 2>/dev/null || echo "requests not installed"
"""
    print(run_ssh("192.168.86.128", "sarvar", "1", commands))
