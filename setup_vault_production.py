#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HashiCorp Vault Enterprise - Universal Production Installer
Qo'llab-quvvatlaydi:
- Ubuntu / Debian (apt-get)
- RHEL / CentOS / Rocky Linux / AlmaLinux / Oracle Linux / Fedora (dnf / yum)
"""

import os
import sys
import subprocess
import shutil
import time
import json

# Ranglar
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

def run_cmd(cmd, check=True):
    return subprocess.run(cmd, shell=True, check=check)

def run_cmd_capture(cmd, check=False):
    return subprocess.run(cmd, shell=True, check=check, text=True, capture_output=True)

def print_step(msg):
    print(f"\n{C_YELLOW}{C_BOLD}▶ {msg}{C_RESET}")

def print_ok(msg):
    print(f"{C_GREEN}✔ {msg}{C_RESET}")

def print_err(msg):
    print(f"{C_RED}✖ {msg}{C_RESET}")

def detect_os():
    """OS turini aniqlash: debian yoki rhel"""
    if shutil.which("dnf"):
        return "rhel", "dnf"
    elif shutil.which("yum"):
        return "rhel", "yum"
    elif shutil.which("apt-get"):
        return "debian", "apt-get"
    return "unknown", ""

def get_server_ip():
    try:
        out = subprocess.check_output("hostname -I", shell=True, text=True).strip()
        if out:
            return out.split()[0]
    except Exception:
        pass
    return "127.0.0.1"

def install_system_packages(os_family, pkg_mgr):
    print_step(f"1. Tizim paketlarini o'rnatish ({pkg_mgr})...")
    if os_family == "rhel":
        run_cmd(f"{pkg_mgr} check-update", check=False)
        run_cmd(f"{pkg_mgr} install -y curl wget jq python3 python3-pip", check=False)
        # requests kutubxonasini o'rnatish
        run_cmd(f"{pkg_mgr} install -y python3-requests", check=False)
        run_cmd("python3 -m pip install --upgrade requests", check=False)
        # firewalld yoki iptables
        run_cmd(f"{pkg_mgr} install -y firewalld", check=False)
    else:
        os.environ["DEBIAN_FRONTEND"] = "noninteractive"
        run_cmd("apt-get update -y")
        run_cmd("apt-get install -y curl wget gpg lsb-release jq ufw python3 python3-pip python3-requests")
    print_ok("Kerakli paketlar o'rnatildi.")

def install_vault_binary(os_family, pkg_mgr):
    print_step("2. HashiCorp rasmiy repozitoriysini qo'shish va Vault o'rnatish...")
    if not shutil.which("vault"):
        if os_family == "rhel":
            # RHEL / CentOS / Rocky / AlmaLinux repozitoriy
            run_cmd("curl -fsSL https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo -o /etc/yum.repos.d/hashicorp.repo")
            run_cmd(f"{pkg_mgr} install -y vault")
        else:
            run_cmd("wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg --yes")
            distro = subprocess.check_output("lsb_release -cs", shell=True, text=True).strip()
            with open("/etc/apt/sources.list.d/hashicorp.list", "w") as f:
                f.write(f"deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com {distro} main\n")
            run_cmd("apt-get update -y")
            run_cmd("apt-get install -y vault")
        print_ok("HashiCorp Vault muvaffaqiyatli o'rnatildi.")
    else:
        ver = subprocess.check_output("vault version", shell=True, text=True).strip()
        print_ok(f"Vault allaqachon mavjud: {ver}")

def configure_firewall(os_family):
    print_step("7. Xavfsizlik Firewall sozlash (Port 22 va 8200)...")
    if os_family == "rhel":
        # firewalld sozlash
        run_cmd("systemctl enable firewalld", check=False)
        run_cmd("systemctl start firewalld", check=False)
        run_cmd("firewall-cmd --permanent --add-port=22/tcp", check=False)
        run_cmd("firewall-cmd --permanent --add-port=8200/tcp", check=False)
        run_cmd("firewall-cmd --reload", check=False)
        print_ok("Firewalld sozlandi: 22 va 8200 portlari ochildi.")
    else:
        # ufw sozlash
        run_cmd("ufw default deny incoming", check=False)
        run_cmd("ufw default allow outgoing", check=False)
        run_cmd("ufw allow 22/tcp comment 'SSH'", check=False)
        run_cmd("ufw allow 8200/tcp comment 'Vault UI and API'", check=False)
        run_cmd("ufw --force enable", check=False)
        print_ok("UFW sozlandi: 22 va 8200 portlari ochildi.")

def main():
    if os.geteuid() != 0:
        print_err("Ushbu skriptni root huquqi bilan ishga tushiring: sudo python3 setup_vault_production.py")
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser(description="HashiCorp Vault Production Installer")
    parser.add_argument("--domain", default="", help="Vault domen manzili (masalan: https://vault-srv.sarvartech.uz)")
    parser.add_argument("--proxy-cidr", default="", help="Reverse Proxy IP yoki CIDR (masalan: 127.0.0.1,10.0.0.0/8)")
    parser.add_argument("-y", "--yes", action="store_true", help="Savollarsiz avtomatik o'rnatish")
    args, _ = parser.parse_known_args()

    default_domain = "https://vault-srv.sarvartech.uz"
    default_proxy = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

    domain = args.domain
    proxy_cidr = args.proxy_cidr

    if not domain:
        if args.yes:
            domain = default_domain
        else:
            d_inp = input(f"Vault Public Domain / URL [{default_domain}]: ").strip()
            domain = d_inp if d_inp else default_domain

    domain = domain.rstrip("/")
    if not domain.startswith("http://") and not domain.startswith("https://"):
        domain = "https://" + domain

    if not proxy_cidr:
        if args.yes:
            proxy_cidr = default_proxy
        else:
            p_inp = input(f"Reverse Proxy IP / CIDR [{default_proxy}]: ").strip()
            proxy_cidr = p_inp if p_inp else default_proxy

    os_family, pkg_mgr = detect_os()
    server_ip = get_server_ip()

    print(f"{C_CYAN}{C_BOLD}" + "="*76)
    print("   🔐 HASHICORP VAULT ENTERPRISE - UNIVERSAL PRODUCTION O'RNATUVCHI")
    print(f"   Domen Manzili:        {domain}")
    print(f"   Aniqlangan OS Turi:   {os_family.upper()} ({pkg_mgr})")
    print(f"   Aniqlangan Server IP: {server_ip}")
    print(f"   Reverse Proxy CIDR:   {proxy_cidr}")
    print("="*76 + f"{C_RESET}")

    # 1. Paketlar
    install_system_packages(os_family, pkg_mgr)

    # 2. Vault o'rnatish
    install_vault_binary(os_family, pkg_mgr)

    # 3. Konfiguratsiya
    print_step("3. Vault konfiguratsiyasi (/etc/vault.d/vault.hcl)...")
    os.makedirs("/opt/vault/data", exist_ok=True)
    os.makedirs("/var/log/vault", exist_ok=True)
    os.makedirs("/var/backups/vault", exist_ok=True)
    
    # User vault mavjudligini tekshirish
    run_cmd("id -u vault &>/dev/null || useradd -r -m -d /opt/vault -s /bin/false vault", check=False)
    run_cmd("chown -R vault:vault /opt/vault /var/log/vault /etc/vault.d", check=False)
    run_cmd("chmod 750 /var/log/vault", check=False)

    hcl_config = f"""ui = true
disable_mlock = true

storage "file" {{
  path = "/opt/vault/data"
}}

listener "tcp" {{
  address     = "0.0.0.0:8200"
  tls_disable = 1
  x_forwarded_for_authorized_addrs = "{proxy_cidr}"
  x_forwarded_for_hop_skips = 0
}}

api_addr = "{domain}"
cluster_addr = "http://{server_ip}:8201"
"""
    with open("/etc/vault.d/vault.hcl", "w") as f:
        f.write(hcl_config)

    run_cmd("systemctl daemon-reload", check=False)
    run_cmd("systemctl enable vault", check=False)
    run_cmd("systemctl restart vault", check=False)
    time.sleep(2)
    print_ok("Vault konfiguratsiya qilindi va ishga tushirildi.")

    # 4. Auto-unseal va muhit
    print_step("4. Auto-Unseal va tizim muhitini sozlash...")
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

    auto_unseal_sh = """#!/bin/bash
export VAULT_ADDR="http://127.0.0.1:8200"
for i in {1..20}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8200/v1/sys/health || echo "000")
    if [ "$STATUS" == "200" ]; then exit 0; fi
    if [ "$STATUS" == "503" ]; then break; fi
    sleep 1
done
if [ -f /etc/vault.d/vault_init.json ]; then
    KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json)
    KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json)
    vault operator unseal "$KEY1" > /dev/null 2>&1
    vault operator unseal "$KEY2" > /dev/null 2>&1
fi
"""
    with open("/usr/local/bin/vault-auto-unseal.sh", "w") as f:
        f.write(auto_unseal_sh)
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
    print_ok("Auto-Unseal xizmati yoqildi.")

    # 5. Initialization / Token
    print_step("5. Vault holati va Root Tokenni tekshirish...")
    os.environ["VAULT_ADDR"] = "http://127.0.0.1:8200"
    init_res = run_cmd_capture("vault status -format=json", check=False)
    is_init = False
    is_sealed = True
    if init_res.returncode in [0, 2]:
        try:
            st = json.loads(init_res.stdout)
            is_init = st.get("initialized", False)
            is_sealed = st.get("sealed", True)
        except Exception:
            pass

    root_token = ""
    if not is_init:
        print_step("Yangi Vault initsializatsiya qilinmoqda...")
        init_run = run_cmd_capture("vault operator init -key-shares=3 -key-threshold=2 -format=json", check=False)
        init_data = json.loads(init_run.stdout)
        with open("/etc/vault.d/vault_init.json", "w") as f:
            json.dump(init_data, f, indent=2)
        run_cmd("chmod 600 /etc/vault.d/vault_init.json", check=False)
        k1 = init_data["unseal_keys_b64"][0]
        k2 = init_data["unseal_keys_b64"][1]
        root_token = init_data["root_token"]
        run_cmd(f"vault operator unseal {k1}", check=False)
        run_cmd(f"vault operator unseal {k2}", check=False)
        print_ok(f"Vault initsializatsiya qilindi! Root Token: {root_token}")
    else:
        print_ok("Vault allaqachon initsializatsiya qilingan.")
        if is_sealed and os.path.exists("/etc/vault.d/vault_init.json"):
            with open("/etc/vault.d/vault_init.json", "r") as f:
                d = json.load(f)
            run_cmd(f"vault operator unseal {d['unseal_keys_b64'][0]}", check=False)
            run_cmd(f"vault operator unseal {d['unseal_keys_b64'][1]}", check=False)

        if os.path.exists("/etc/vault.d/vault_init.json"):
            with open("/etc/vault.d/vault_init.json", "r") as f:
                root_token = json.load(f).get("root_token", "")
        if not root_token:
            root_token = input("Mavjud Root Tokenni kiriting: ").strip()

    os.environ["VAULT_TOKEN"] = root_token

    # 6. Enginelar va Audit
    print_step("6. Secret Enginelar va Audit logni faollashtirish...")
    run_cmd(f"VAULT_TOKEN='{root_token}' vault secrets enable -path=secret kv-v2", check=False)
    run_cmd(f"VAULT_TOKEN='{root_token}' vault auth enable approle", check=False)
    run_cmd(f"VAULT_TOKEN='{root_token}' vault auth enable userpass", check=False)

    run_cmd("touch /var/log/vault/vault_audit.log")
    run_cmd("chown vault:vault /var/log/vault/vault_audit.log", check=False)
    run_cmd("chmod 644 /var/log/vault/vault_audit.log", check=False)
    run_cmd(f"VAULT_TOKEN='{root_token}' vault audit enable file file_path=/var/log/vault/vault_audit.log", check=False)
    print_ok("Enginelar va Audit log yoqildi.")

    # 7. Firewall
    configure_firewall(os_family)

    # 8. CLI-Panel
    print_step("8. CLI-Panelni o'rnatish (/usr/local/bin/vault-panel)...")
    src_panel = "./vault_panel.py" if os.path.exists("./vault_panel.py") else "/tmp/vault_panel.py"
    if os.path.exists(src_panel):
        shutil.copy(src_panel, "/usr/local/bin/vault-panel.py")
        run_cmd("chmod +x /usr/local/bin/vault-panel.py")
        with open("/usr/local/bin/vault-panel", "w") as f:
            f.write("#!/bin/bash\nexec python3 /usr/local/bin/vault-panel.py \"$@\"\n")
        run_cmd("chmod +x /usr/local/bin/vault-panel")
        print_ok("CLI-Panel muvaffaqiyatli o'rnatildi: buyruq -> vault-panel")

    print("\n" + f"{C_GREEN}{C_BOLD}" + "="*76)
    print("✔ BARCHA SOZLAMALAR VA DEPENDENCY'LAR MUVAFFAQIYATLI O'RNATILDI!")
    print("="*76 + f"{C_RESET}")
    print(f"  Web UI (Domain): {domain}/ui")
    print(f"  Web UI (Direct): http://{server_ip}:8200/ui")
    print(f"  CLI-Panel:       vault-panel (istalgan joydan ishlaydi)")
    print(f"  Root Token:      {root_token}")
    print("="*76)

if __name__ == '__main__':
    main()
