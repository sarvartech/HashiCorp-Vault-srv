import paramiko
import sys

def run_ssh(host, user, password, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=10)
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    if "sudo" in cmd:
        stdin.write(password + "\n")
        stdin.flush()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    client.close()
    return out, err

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.88.18"
    out, err = run_ssh(host, "sarvar", "1", "sudo -S uname -a && cat /etc/os-release")
    print(out)
