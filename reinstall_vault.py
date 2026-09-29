#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HashiCorp Vault Enterprise - 1-Click Production Re-Installer with Domain & Proxy Support
Domen va Reverse Proxy (Nginx / HAProxy / F5) bilan ishlash uchun to'liq moslashtirilgan.
Eski/qulflangan bazani tozalab, noldan yangi kalitlar bilan to'liq qayta o'rnatadi.
"""

import os
import sys
import subprocess
import shutil
import time
import json
import argparse

C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

DEFAULT_DOMAIN = "https://vault-srv.sarvartech.uz"
DEFAULT_PROXY_CIDRS = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

def run_cmd(cmd, check=True):
    return subprocess.run(cmd, shell=True, check=check, text=True, capture_output=True)

def print_step(msg):
    print(f"\n{C_YELLOW}{C_BOLD}▶ {msg}{C_RESET}")

def print_ok(msg):
    print(f"{C_GREEN}✔ {msg}{C_RESET}")

def get_server_ip():
    try:
        out = subprocess.check_output("hostname -I", shell=True, text=True).strip()
        if out:
            return out.split()[0]
    except Exception:
        pass
    return "127.0.0.1"

def reinstall_vault(domain: str, proxy_cidrs: str):
    if os.geteuid() != 0:
        print(f"{C_RED}✖ Ushbu skriptni root huquqi bilan ishga tushiring: sudo python3 reinstall_vault.py{C_RESET}")
        sys.exit(1)

    server_ip = get_server_ip()

    print(f"{C_CYAN}{C_BOLD}" + "="*76)
    print("   🔄 HASHICORP VAULT ENTERPRISE - RE-INSTALL (DOMAIN & REVERSE PROXY)")
    print(f"   Domain Manzili:       {domain}")
    print(f"   Lokal Server IP:      {server_ip}")
    print(f"   Proxy Whitelist CIDR: {proxy_cidrs}")
    print("="*76 + f"{C_RESET}")

    # 1. Stop and Wipe
    print_step("1. Vault xizmatini to'xtatish va eski ma'lumotlarni tozalash...")
    run_cmd("systemctl stop vault", check=False)
    run_cmd("systemctl stop vault-auto-unseal", check=False)
    run_cmd("rm -rf /opt/vault/data/* /etc/vault.d/vault_init.json /var/log/vault/*", check=False)
    os.makedirs("/opt/vault/data", exist_ok=True)
    os.makedirs("/var/log/vault", exist_ok=True)
    run_cmd("id -u vault &>/dev/null || useradd -r -m -d /opt/vault -s /bin/false vault", check=False)
    run_cmd("chown -R vault:vault /opt/vault /var/log/vault /etc/vault.d", check=False)
    run_cmd("chmod 750 /var/log/vault", check=False)
    print_ok("Eski ma'lumotlar tozalandi.")

    # 2. Config & Restart
    print_step("2. vault.hcl konfiguratsiyasini domen va proxy sozlamalari bilan yangilash...")
    hcl = f"""ui = true
disable_mlock = true

storage "file" {{
  path = "/opt/vault/data"
}}

listener "tcp" {{
  address     = "0.0.0.0:8200"
  tls_disable = 1
  x_forwarded_for_authorized_addrs = "{proxy_cidrs}"
  x_forwarded_for_hop_skips = 0
}}

api_addr = "{domain}"
cluster_addr = "http://{server_ip}:8201"
"""
    with open("/etc/vault.d/vault.hcl", "w") as f:
        f.write(hcl)
    run_cmd("chown -R vault:vault /etc/vault.d")
    
    # 3. Environment Variables
    print_step("3. Tizim muhit o'zgaruvchilarini sozlash (/etc/environment va /etc/profile.d/vault.sh)...")
    env_lines = [
        'export VAULT_ADDR="http://127.0.0.1:8200"',
        f'export VAULT_PUBLIC_ADDR="{domain}"'
    ]
    try:
        with open("/etc/environment", "r") as f:
            cur_env = f.read()
    except Exception:
        cur_env = ""
        
    with open("/etc/environment", "w") as f:
        filtered = [l for l in cur_env.splitlines() if not l.startswith("export VAULT_ADDR") and not l.startswith("export VAULT_PUBLIC_ADDR")]
        filtered.extend(env_lines)
        f.write("\n".join(filtered) + "\n")

    profile_sh = f"""#!/bin/bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_PUBLIC_ADDR="{domain}"
if [ -f /etc/vault.d/vault_init.json ]; then
    export VAULT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json 2>/dev/null)
fi
"""
    with open("/etc/profile.d/vault.sh", "w") as f:
        f.write(profile_sh)
    run_cmd("chmod +x /etc/profile.d/vault.sh")

    run_cmd("systemctl daemon-reload", check=False)
    run_cmd("systemctl enable vault", check=False)
    run_cmd("systemctl restart vault", check=False)
    time.sleep(2)
    print_ok("Vault domen sozlamalari bilan ishga tushirildi.")

    # 4. Fresh Initialization
    print_step("4. Yangi kalitlar bilan initsializatsiya qilish (Fresh Init)...")
    os.environ["VAULT_ADDR"] = "http://127.0.0.1:8200"
    os.environ["VAULT_PUBLIC_ADDR"] = domain
    
    init_res = run_cmd("vault operator init -key-shares=3 -key-threshold=2 -format=json")
    if init_res.returncode != 0:
        print(f"{C_RED}✖ Init xatoligi: {init_res.stderr}{C_RESET}")
        sys.exit(1)
        
    init_data = json.loads(init_res.stdout)
    with open("/etc/vault.d/vault_init.json", "w") as f:
        json.dump(init_data, f, indent=2)
    run_cmd("chmod 600 /etc/vault.d/vault_init.json")

    k1 = init_data["unseal_keys_b64"][0]
    k2 = init_data["unseal_keys_b64"][1]
    k3 = init_data["unseal_keys_b64"][2]
    root_token = init_data["root_token"]

    # 5. Unseal
    print_step("5. Vaultni yangi kalitlar bilan ochish (Unseal)...")
    run_cmd(f"vault operator unseal {k1}")
    run_cmd(f"vault operator unseal {k2}")
    print_ok("Vault muvaffaqiyatli ochildi (Unsealed)!")

    # 6. Enable Engines & Audit
    print_step("6. Secret Enginelar, Auth va Audit Logini yoqish...")
    run_cmd(f"VAULT_TOKEN='{root_token}' vault secrets enable -path=secret kv-v2", check=False)
    run_cmd(f"VAULT_TOKEN='{root_token}' vault auth enable approle", check=False)
    run_cmd(f"VAULT_TOKEN='{root_token}' vault auth enable userpass", check=False)

    run_cmd("touch /var/log/vault/vault_audit.log")
    run_cmd("chown vault:vault /var/log/vault/vault_audit.log", check=False)
    run_cmd("chmod 644 /var/log/vault/vault_audit.log", check=False)
    run_cmd(f"VAULT_TOKEN='{root_token}' vault audit enable file file_path=/var/log/vault/vault_audit.log", check=False)
    print_ok("KV-v2, AppRole, Userpass va Audit log faollashtirildi.")

    # 7. Auto-unseal service
    print_step("7. Avtomatik ochish xizmatini (Auto-Unseal) sozlash...")
    auto_sh = f"""#!/bin/bash
export VAULT_ADDR="http://127.0.0.1:8200"
for i in {{1..25}}; do
    STATUS=$(curl -s -o /dev/null -w "%{{http_code}}" http://127.0.0.1:8200/v1/sys/health || echo "000")
    if [ "$STATUS" == "200" ]; then exit 0; fi
    if [ "$STATUS" == "503" ]; then break; fi
    sleep 1
done
if [ -f /etc/vault.d/vault_init.json ]; then
    KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json 2>/dev/null)
    KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json 2>/dev/null)
    if [ -n "$KEY1" ] && [ -n "$KEY2" ]; then
        vault operator unseal "$KEY1" > /dev/null 2>&1
        vault operator unseal "$KEY2" > /dev/null 2>&1
    fi
fi
"""
    with open("/usr/local/bin/vault-auto-unseal.sh", "w") as f:
        f.write(auto_sh)
    run_cmd("chmod +x /usr/local/bin/vault-auto-unseal.sh")

    unit_content = """[Unit]
Description=Auto Unseal HashiCorp Vault
After=vault.service
Wants=vault.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vault-auto-unseal.sh
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/vault-auto-unseal.service", "w") as f:
        f.write(unit_content)
    run_cmd("systemctl daemon-reload", check=False)
    run_cmd("systemctl enable vault-auto-unseal.service", check=False)
    run_cmd("systemctl restart vault-auto-unseal.service", check=False)
    print_ok("Auto-Unseal yangilandi va ishga tushirildi.")

    # 8. Save credentials file
    print_step("8. Kalitlar va ma'lumotlarni saqlash...")
    cred_text = f"""==================================================
           HASHICORP VAULT PRODUCTION CREDENTIALS
==================================================
Domain URL:   {domain}
Web UI URL:   {domain}/ui
Local API:    http://127.0.0.1:8200
Server IP:    {server_ip}:8200

Root Token:
{root_token}

Unseal Key 1:
{k1}

Unseal Key 2:
{k2}

Unseal Key 3:
{k3}
==================================================
"""
    with open("/root/vault_credentials.txt", "w") as f:
        f.write(cred_text)
    run_cmd("chmod 600 /root/vault_credentials.txt")

    # Foydalanuvchilar papkalariga ham nusxalash
    if os.path.exists("/home"):
        for u in os.listdir("/home"):
            u_home = os.path.join("/home", u)
            if os.path.isdir(u_home):
                u_cred = os.path.join(u_home, "vault_credentials.txt")
                try:
                    with open(u_cred, "w") as f:
                        f.write(cred_text)
                    run_cmd(f"chown {u}:{u} {u_cred}", check=False)
                    run_cmd(f"chmod 600 {u_cred}", check=False)
                except Exception:
                    pass
    print_ok("Kalitlar /root/vault_credentials.txt fayliga saqlandi.")

    # 9. Setup CLI-Panel
    print_step("9. CLI-Panelni o'rnatish...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_panel = os.path.join(script_dir, "vault_panel.py")
    if not os.path.exists(src_panel):
        src_panel = "/tmp/vault_panel.py"

    if os.path.exists(src_panel):
        shutil.copy(src_panel, "/usr/local/bin/vault-panel.py")
        run_cmd("chmod +x /usr/local/bin/vault-panel.py")
        with open("/usr/local/bin/vault-panel", "w") as f:
            f.write('#!/bin/bash\nexec python3 /usr/local/bin/vault-panel.py "$@"\n')
        run_cmd("chmod +x /usr/local/bin/vault-panel")
        print_ok("CLI-Panel o'rnatildi: buyruq -> vault-panel")

    # 10. Firewall
    print_step("10. Firewall sozlamalari (Port 22 va 8200)...")
    if shutil.which("ufw"):
        run_cmd("ufw allow 22/tcp comment 'SSH'", check=False)
        run_cmd("ufw allow 8200/tcp comment 'Vault UI and API'", check=False)
        run_cmd("ufw --force enable", check=False)
        print_ok("UFW: 22 va 8200 portlari ochildi.")
    elif shutil.which("firewall-cmd"):
        run_cmd("firewall-cmd --permanent --add-port=22/tcp", check=False)
        run_cmd("firewall-cmd --permanent --add-port=8200/tcp", check=False)
        run_cmd("firewall-cmd --reload", check=False)
        print_ok("Firewalld: 22 va 8200 portlari ochildi.")

    print("\n" + f"{C_GREEN}{C_BOLD}" + "="*76)
    print("✔ HASHICORP VAULT DOMEN BILAN TO'LIQ QAYTA O'RNATILDI!")
    print("="*76 + f"{C_RESET}")
    print(f"  🌐 Domen Manzili (URL): {domain}")
    print(f"  💻 Web UI manzili:      {domain}/ui")
    print(f"  🔑 Root Token:          {root_token}")
    print(f"  🗝️  Unseal Key 1:        {k1}")
    print(f"  🗝️  Unseal Key 2:        {k2}")
    print("="*76)
    print(f"\n{C_YELLOW}Test qilish buyrug'i:{C_RESET}")
    print(f"  curl -k -s -H \"X-Vault-Token: {root_token}\" {domain}/v1/secret/config")
    print(f"\n{C_CYAN}CLI-Panelni ishga tushirish uchun istalgan joyda:{C_RESET} {C_BOLD}vault-panel{C_RESET}\n")

    launch = input("CLI-Panelni darhol ishga tushirasizmi? (ha/yo'q) [ha]: ").strip().lower()
    if launch in ['', 'ha', 'yes', 'y']:
        os.system(f"export VAULT_ADDR='http://127.0.0.1:8200' VAULT_PUBLIC_ADDR='{domain}' VAULT_TOKEN='{root_token}'; vault-panel")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HashiCorp Vault Re-installer with Domain Support")
    parser.add_argument("--domain", default="", help="Vault domen manzili (masalan: https://vault-srv.sarvartech.uz)")
    parser.add_argument("--proxy-cidr", default="", help="Reverse Proxy IP yoki CIDR (masalan: 127.0.0.1,10.0.0.0/8)")
    parser.add_argument("-y", "--yes", action="store_true", help="Savollarsiz to'g'ridan-to'g'ri o'rnatish")
    args = parser.parse_args()

    domain = args.domain
    proxy_cidr = args.proxy_cidr

    if not domain:
        if args.yes:
            domain = DEFAULT_DOMAIN
        else:
            print(f"{C_CYAN}{C_BOLD}HashiCorp Vault Production Re-Installer{C_RESET}")
            d_input = input(f"Vault Domen / URL manzili [{DEFAULT_DOMAIN}]: ").strip()
            domain = d_input if d_input else DEFAULT_DOMAIN

    domain = domain.rstrip("/")
    if not domain.startswith("http://") and not domain.startswith("https://"):
        domain = "https://" + domain

    if not proxy_cidr:
        if args.yes:
            proxy_cidr = DEFAULT_PROXY_CIDRS
        else:
            p_input = input(f"Reverse Proxy IP / CIDR manzillari [{DEFAULT_PROXY_CIDRS}]: ").strip()
            proxy_cidr = p_input if p_input else DEFAULT_PROXY_CIDRS

    reinstall_vault(domain, proxy_cidr)
