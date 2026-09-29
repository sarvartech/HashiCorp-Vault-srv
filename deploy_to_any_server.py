#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy HashiCorp Vault, all dependencies, configs, and CLI-Panel to ANY server.
"""

import os
import sys
import paramiko

def deploy_to_server(host, user, password, root_token="", domain="https://vault-srv.sarvartech.uz", mode="1"):
    print(f"\n=======================================================")
    print(f"🚀 {host} SERVERIGA O'RNATISH BOSHLANDI (Domain: {domain})...")
    print(f"=======================================================")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password, timeout=20)
    except Exception as e:
        print(f"❌ Serverga ulanishda xatolik: {e}")
        return False
        
    sftp = client.open_sftp()
    
    # 1. Upload setup files
    script_dir = os.path.dirname(__file__)
    for fname in ["setup_vault_production.sh", "reinstall_vault.py", "vault_panel.py"]:
        fpath = os.path.join(script_dir, fname)
        if os.path.exists(fpath):
            sftp.put(fpath, f"/tmp/{fname}")
            sftp.chmod(f"/tmp/{fname}", 0o755)
    
    sftp.close()
    
    # 2. Execute installation or clean reinstall
    env_vars = f"export VAULT_DOMAIN='{domain}' export VAULT_PUBLIC_ADDR='{domain}';"
    if root_token:
        env_vars += f" export VAULT_TOKEN='{root_token}';"
        
    if mode == "2":
        # Full clean reinstall
        runner = f"{env_vars} python3 /tmp/reinstall_vault.py --domain '{domain}' -y"
    else:
        # Standard setup
        runner = f"{env_vars} bash /tmp/setup_vault_production.sh"
        
    if user == "root":
        cmd = runner
    else:
        cmd = f"echo {password} | sudo -S bash -c \"{runner}\""
        
    print("Paketlar o'rnatilmoqda va konfiguratsiyalar qo'llanilmoqda...")
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    client.close()
    print("\n✔ Jarayon muvaffaqiyatli yakunlandi!")
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("  VAULT PRODUCTION MASOFAVIY BOSHQARUVCHI (DEPLOYER)")
    print("=" * 60)
    print("Amalni tanlang:")
    print("  [1] Oddiy o'rnatish / Mavjud tizimni yangilash")
    print("  [2] To'liq Qayta Re-install (Eski bazani tozalab, Domain bilan yangilash)")
    mode = input("Tanlang [1-2] [default: 2]: ").strip() or "2"
    
    target_ip = input("\nServer IP manzili [192.168.88.18]: ").strip() or "192.168.88.18"
    target_user = input("SSH foydalanuvchi [root]: ").strip() or "root"
    target_pass = input("SSH paroli: ").strip()
    target_domain = input("Vault Domeni / URL [https://vault-srv.sarvartech.uz]: ").strip() or "https://vault-srv.sarvartech.uz"
    target_token = input("Mavjud Root Token (ixtiyoriy, yangi yaratilsa bo'sh qoldiring): ").strip()
    
    if target_ip and target_pass:
        deploy_to_server(target_ip, target_user, target_pass, target_token, target_domain, mode)
    else:
        print("IP va parol kiritilmadi!")
