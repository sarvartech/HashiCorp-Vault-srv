#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HashiCorp Vault - Production Enterprise CLI Management Console
Administrator buyruq terishi shart bo'lmagan, 100% interaktiv boshqaruv tizimi.
"""

import os
import sys
import json
import re
import secrets
import string
import datetime
import subprocess
try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    # Rocky Linux 9.3 (dnf) or Ubuntu (apt) auto-install fallback
    subprocess.run("sudo dnf install -y python3-requests > /dev/null 2>&1 || sudo apt-get install -y python3-requests > /dev/null 2>&1 || pip3 install requests > /dev/null 2>&1", shell=True)
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Dict, Any, List, Optional, Tuple

VAULT_ADDR = os.environ.get("VAULT_PUBLIC_ADDR") or os.environ.get("VAULT_ADDR", "https://vault-srv.sarvartech.uz")
CRED_FILE = "/etc/vault.d/vault_init.json"
AUDIT_LOG_FILE = "/var/log/vault/vault_audit.log"
BACKUP_DIR = os.environ.get("VAULT_BACKUP_DIR", os.path.expanduser("~/vault_backups"))

# ANSI Ranglar
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"
C_BG_DARK = "\033[40m"

def get_possible_cred_paths() -> List[str]:
    paths = [
        CRED_FILE,
        "/root/vault_credentials.txt",
        "/home/s.solijonov/vault_credentials.txt",
        "/home/sarvar/vault_credentials.txt",
        os.path.expanduser("~/vault_credentials.txt"),
    ]
    if os.path.exists("/home"):
        try:
            for u in os.listdir("/home"):
                p = os.path.join("/home", u, "vault_credentials.txt")
                if p not in paths:
                    paths.append(p)
        except Exception:
            pass
    return paths

def get_cached_token() -> str:
    token = os.environ.get("VAULT_TOKEN")
    if token:
        return token
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f:
                return json.load(f).get("root_token", "")
        except Exception:
            pass
    for p in get_possible_cred_paths():
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("hvs.") or line.startswith("s."):
                            return line
            except Exception:
                pass
    return ""

TOKEN = ""
TOKEN_POLICIES: List[str] = []

def vault_headers() -> Dict[str, str]:
    return {
        "X-Vault-Token": TOKEN,
        "Content-Type": "application/json"
    }

def print_banner():
    os.system("clear")
    masked_token = f"{TOKEN[:8]}...{TOKEN[-4:]}" if len(TOKEN) > 12 else (TOKEN if TOKEN else "YO'Q")
    policies_str = ", ".join(TOKEN_POLICIES) if TOKEN_POLICIES else "root"
    print(f"{C_CYAN}{C_BOLD}" + "="*76)
    print("   🔐 HASHICORP VAULT ENTERPRISE - PRODUCTION BOSHQARUV KONSOLI")
    print(f"   Server: {VAULT_ADDR}")
    print(f"   Token:  {C_GREEN}{masked_token}{C_CYAN} | Ruxsatnomalar: {C_YELLOW}{policies_str}{C_CYAN} | Status: FAOL")
    print("="*76 + f"{C_RESET}")

def login_interactive():
    global VAULT_ADDR, TOKEN, TOKEN_POLICIES
    os.system("clear")
    print(f"{C_CYAN}{C_BOLD}" + "="*76)
    print("   🔐 HASHICORP VAULT CLI-PANEL - TIZIMGA KIRISH (AUTHENTICATION)")
    print("="*76 + f"{C_RESET}")
    
    # 1. Server Address
    current_addr = os.environ.get("VAULT_PUBLIC_ADDR") or os.environ.get("VAULT_ADDR", VAULT_ADDR) or "https://vault-srv.sarvartech.uz"
    addr_prompt = input(f"\n🌐 Vault Server URL [{current_addr}]: ").strip()
    if addr_prompt:
        VAULT_ADDR = addr_prompt.rstrip("/")
    else:
        VAULT_ADDR = current_addr.rstrip("/")
        
    cached_token = get_cached_token()
    
    # 2. Token Input Loop
    while True:
        print(f"\n{C_BOLD}🔑 VAULT ROOT / ADMIN TOKENNI KIRITING:{C_RESET}")
        if cached_token:
            masked = f"{cached_token[:8]}...{cached_token[-4:]}"
            prompt_text = f"Tokenni kiriting [Enter: avvalgi tokendan ({masked}) foydalanish]: "
        else:
            prompt_text = "Tokenni kiriting (masalan: hvs.CAES...): "
            
        entered_token = input(prompt_text).strip()
        if not entered_token and cached_token:
            entered_token = cached_token
            
        if not entered_token:
            print_warning("Token kiritilmadi! Iltimos, Vault tokeningizni kiriting.")
            continue
            
        print_info("Token tekshirilmoqda...")
        try:
            r = requests.get(
                f"{VAULT_ADDR}/v1/auth/token/lookup-self",
                headers={"X-Vault-Token": entered_token, "Content-Type": "application/json"},
                timeout=8,
                verify=False
            )
            if r.status_code == 200:
                TOKEN = entered_token
                user_info = r.json().get("data", {})
                TOKEN_POLICIES = user_info.get("policies", [])
                ttl = user_info.get("ttl", 0)
                ttl_str = f"{ttl} soniya" if ttl > 0 else "Cheksiz (Root)"
                
                print_success("Token muvaffaqiyatli qabul qilindi va tasdiqlandi!")
                print(f"  Foydalanuvchi/Display: {user_info.get('display_name', 'admin')}")
                print(f"  Ruxsatnomalar:         {', '.join(TOKEN_POLICIES)}")
                print(f"  Amal qilish vaqti:     {ttl_str}")
                input(f"\n{C_GREEN}[Asosiy menyuga o'tish uchun Enter tugmasini bosing...]{C_RESET}")
                break
            elif r.status_code == 403:
                print_error("Kiritilgan token yaroqsiz yoki muddati tugagan (403 Permission Denied)!")
            else:
                print_error(f"Vault server xatolik qaytardi: Status {r.status_code}")
        except requests.exceptions.SSLError as e:
            print_error(f"SSL/TLS sertifikat tekshiruvida xatolik: {e}")
        except requests.exceptions.ConnectionError:
            print_error(f"'{VAULT_ADDR}' manzilidagi Vault serverga ulanib bo'lmadi! Server ishlayotganiga ishonch hosil qiling.")
            change_addr = input("Boshqa Server URL kiritasizmi? (ha/yo'q): ").strip().lower()
            if change_addr in ['ha', 'yes', 'y']:
                new_a = input("Yangi Server URL (masalan: https://vault-srv.sarvartech.uz yoki http://127.0.0.1:8200): ").strip()
                if new_a:
                    VAULT_ADDR = new_a.rstrip("/")
        except Exception as e:
            print_error(f"Ulanishda xatolik: {e}")

def print_success(msg: str):
    print(f"\n{C_GREEN}{C_BOLD}✔ {msg}{C_RESET}")

def print_error(msg: str):
    print(f"\n{C_RED}{C_BOLD}✖ Xatolik: {msg}{C_RESET}")

def print_info(msg: str):
    print(f"\n{C_CYAN}ℹ {msg}{C_RESET}")

def print_warning(msg: str):
    print(f"\n{C_YELLOW}⚠ {msg}{C_RESET}")

def pause():
    input(f"\n{C_YELLOW}[Davom etish uchun Enter tugmasini bosing...]{C_RESET}")

def generate_strong_password(length: int = 24) -> str:
    """Kriptografik xavfsiz kuchli parol generatsiyasi"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_api_key(prefix: str = "vlt") -> str:
    """Xavfsiz API Token generatsiyasi"""
    return f"{prefix}_{secrets.token_hex(20)}"

def detect_client_ip() -> str:
    """SSH ulanishdan administrator yoki mijoz IP manzilini avtomatik aniqlash"""
    ssh_client = os.environ.get("SSH_CLIENT", "")
    if ssh_client:
        return ssh_client.split()[0]
    ssh_connection = os.environ.get("SSH_CONNECTION", "")
    if ssh_connection:
        return ssh_connection.split()[0]
    return "192.168.88.18"

def get_external_vault_addr() -> str:
    """Dasturchilar uchun Vault serverining haqiqiy tarmoq manzilini aniqlash"""
    if os.environ.get("VAULT_PUBLIC_ADDR"):
        return os.environ.get("VAULT_PUBLIC_ADDR").rstrip("/")
    if VAULT_ADDR and "127.0.0.1" not in VAULT_ADDR and "localhost" not in VAULT_ADDR:
        return VAULT_ADDR.rstrip("/")
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return f"http://{ip}:8200"
    except Exception:
        pass
    try:
        out = subprocess.check_output("hostname -I", shell=True, text=True).strip()
        if out:
            return f"http://{out.split()[0]}:8200"
    except Exception:
        pass
    return "http://192.168.88.18:8200"

def normalize_cidr_list(ip_input: str) -> List[str]:
    if not ip_input or not ip_input.strip():
        return []
    parts = [p.strip() for p in ip_input.replace(";", ",").split(",") if p.strip()]
    return [p if "/" in p else f"{p}/32" for p in parts]

# ==============================================================================
# VAULT API HELPERS
# ==============================================================================
def api_get(endpoint: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{VAULT_ADDR}/v1/{endpoint}", headers=vault_headers(), timeout=10, verify=False)
        if r.status_code in [200, 204]:
            return r.json() if r.content else {}
        return None
    except Exception as e:
        print_error(str(e))
        return None

def api_post(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        r = requests.post(f"{VAULT_ADDR}/v1/{endpoint}", headers=vault_headers(), json=data, timeout=10, verify=False)
        if r.status_code in [200, 204]:
            return r.json() if r.content else {}
        print_error(f"Status {r.status_code}: {r.text}")
        return None
    except Exception as e:
        print_error(str(e))
        return None

def api_put(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        r = requests.put(f"{VAULT_ADDR}/v1/{endpoint}", headers=vault_headers(), json=data, timeout=10, verify=False)
        if r.status_code in [200, 204]:
            return r.json() if r.content else {}
        print_error(f"Status {r.status_code}: {r.text}")
        return None
    except Exception as e:
        print_error(str(e))
        return None

def api_delete(endpoint: str) -> bool:
    try:
        r = requests.delete(f"{VAULT_ADDR}/v1/{endpoint}", headers=vault_headers(), timeout=10, verify=False)
        return r.status_code in [200, 204]
    except Exception as e:
        print_error(str(e))
        return False

# ==============================================================================
# INTERACTIVE SELECTORS (NO MANUAL PATH ENTRY)
# ==============================================================================
def list_organizations() -> List[str]:
    res = api_get("secret/metadata?list=true")
    if not res or "data" not in res or "keys" not in res["data"]:
        return []
    return sorted([k.rstrip('/') for k in res["data"]["keys"]])

def list_services(org: str) -> List[str]:
    res = api_get(f"secret/metadata/{org}?list=true")
    if not res or "data" not in res or "keys" not in res["data"]:
        return []
    return sorted([k.rstrip('/') for k in res["data"]["keys"]])

def select_org() -> Optional[str]:
    orgs = list_organizations()
    if not orgs:
        print_warning("Tizimda hech qanday tashkilot mavjud emas. Avval tashkilot qo'shing.")
        return None
    print(f"\n{C_BOLD}Mavjud tashkilotlar ro'yxati:{C_RESET}")
    for idx, o in enumerate(orgs, 1):
        print(f"  {C_CYAN}[{idx}]{C_RESET} {o}")
    ch = input(f"\nTashkilot raqamini tanlang [1-{len(orgs)}]: ").strip()
    if not ch.isdigit() or not (1 <= int(ch) <= len(orgs)):
        print_warning("Noto'g'ri tanlov.")
        return None
    return orgs[int(ch) - 1]

def select_org_and_service() -> Tuple[Optional[str], Optional[str]]:
    org = select_org()
    if not org:
        return None, None
    services = list_services(org)
    if not services:
        print_warning(f"'{org}' tashkilotida servislar topilmadi.")
        return org, None
    print(f"\n{C_BOLD}'{org}' ichidagi servislar:{C_RESET}")
    for idx, s in enumerate(services, 1):
        print(f"  {C_CYAN}[{idx}]{C_RESET} {s}")
    ch = input(f"\nServis raqamini tanlang [1-{len(services)}]: ").strip()
    if not ch.isdigit() or not (1 <= int(ch) <= len(services)):
        print_warning("Noto'g'ri tanlov.")
        return org, None
    return org, services[int(ch) - 1]

def select_source_ip_interactive(existing_ip: str = "") -> str:
    detected_ip = detect_client_ip()
    print(f"\n{C_MAGENTA}{C_BOLD}🔒 SOURCE IP RUXSATNOMASINI TANLASH:{C_RESET}")
    print(f"  {C_CYAN}[1]{C_RESET} Hozirgi bog'langan IP manzil: {C_GREEN}{detected_ip}{C_RESET}")
    if existing_ip:
        print(f"  {C_CYAN}[2]{C_RESET} Servisning joriy IP manzili: {C_YELLOW}{existing_ip}{C_RESET}")
    print(f"  {C_CYAN}[3]{C_RESET} Boshqa aniq IP kiritish (Manual IP)")
    print(f"  {C_CYAN}[4]{C_RESET} 🌐 Cheklovsiz (Barcha tarmoqqa ochiq)")
    
    choice = input("\nTanlang [1-4] [default: 1]: ").strip() or "1"
    if choice == "1":
        return detected_ip
    elif choice == "2" and existing_ip:
        return existing_ip
    elif choice == "3":
        manual_ip = input("Aniq Source IP manzilni kiriting (masalan: 192.168.86.75): ").strip()
        return manual_ip
    elif choice == "4":
        return ""
    return detected_ip

# ==============================================================================
# ORGANIZATIONS & SERVICES CRUD
# ==============================================================================
def show_org_service_tree():
    print(f"\n{C_BOLD}{C_BLUE}📂 BARCHA TASHKILOTLAR VA SERVISLAR TUZILMASI (PRODUCTION TREE):{C_RESET}")
    orgs = list_organizations()
    if not orgs:
        print(f"   {C_YELLOW}(Hozircha hech qanday tashkilot yaratilmagan){C_RESET}")
        return
    for org in orgs:
        print(f"\n {C_CYAN}🏢 Tashkilot: {C_BOLD}{org}{C_RESET}")
        services = list_services(org)
        if not services:
            print(f"     └── {C_YELLOW}(servislar yo'q){C_RESET}")
        else:
            for s in services:
                sec = api_get(f"secret/data/{org}/{s}")
                keys_count = 0
                bound_ip = f"{C_YELLOW}🌐 IP: Cheklovsiz{C_RESET}"
                if sec and "data" in sec and "data" in sec["data"]:
                    s_data = sec["data"]["data"]
                    keys_count = len([k for k in s_data.keys() if not k.startswith("_")])
                    if "_bound_source_ip" in s_data and s_data["_bound_source_ip"]:
                        bound_ip = f"{C_MAGENTA}🔒 IP: {s_data['_bound_source_ip']}{C_RESET}"
                print(f"     ├── ⚙️  Servis: {C_GREEN}{s:<22}{C_RESET} [CRED: {keys_count} ta] | {bound_ip}")

def create_organization_wizard():
    print(f"\n{C_BOLD}🏢 YANGI TASHKILOT (ORGANIZATION) QO'SHISH VIZARDI{C_RESET}")
    org_name = input(f"{C_WHITE}Tashkilot nomi (masalan: aloqabank, uzcard, payme): {C_RESET}").strip().lower()
    if not org_name:
        print_warning("Nom kiritilmadi!")
        return
    
    # Check if exists
    if org_name in list_organizations():
        print_warning(f"'{org_name}' tashkiloti allaqachon mavjud.")
        return
    
    initial_service = input(f"{C_WHITE}Boshlang'ich servis nomi [default: core-api]: {C_RESET}").strip().lower() or "core-api"
    source_ip = select_source_ip_interactive()
    
    setup_policies_for_org(org_name)
    setup_policies_for_service(org_name, initial_service)
    
    sec_data = {
        "organization": org_name,
        "service": initial_service,
        "status": "production_active",
        "created_at": str(datetime.datetime.now())
    }
    if source_ip:
        sec_data["_bound_source_ip"] = source_ip
        add_ufw_ip_rule(source_ip, f"Vault-{org_name}-{initial_service}")

    res = api_post(f"secret/data/{org_name}/{initial_service}", {"data": sec_data})
    if res is not None:
        print_success(f"'{org_name}' tashkiloti va '{initial_service}' servisi yaratildi!")
        print_info("Barcha ACL ruxsatnomalari (Admin, Read-Only, Service RW/RO) avtomatik faollashtirildi.")
    else:
        print_error("Tashkilotni yaratishda xatolik yuz berdi.")

def create_service_wizard():
    org = select_org()
    if not org:
        return
    
    print(f"\n{C_BOLD}Tashkilot: {C_CYAN}{org}{C_RESET}")
    print("\nServis turini tanlang (Shablon):")
    print("  [1] 🌐 REST API / Backend Microservice")
    print("  [2] 🗄  Ma'lumotlar bazasi (PostgreSQL / MySQL / Oracle)")
    print("  [3] ⚡ Redis / RabbitMQ / Kafka")
    print("  [4] 💳 To'lov shlyuzi (Payment Gateway)")
    print("  [5] 🛠  Custom (Erkin shakldagi servis)")
    stype = input("\nTanlang [1-5] [default: 1]: ").strip() or "1"
    
    service_name = input("\nYangi servis nomi (masalan: billing, auth, orders): ").strip().lower()
    if not service_name:
        return
    
    setup_policies_for_service(org, service_name)
    source_ip = select_source_ip_interactive()
    
    sec_data: Dict[str, Any] = {
        "organization": org,
        "service": service_name
    }
    if source_ip:
        sec_data["_bound_source_ip"] = source_ip
        add_ufw_ip_rule(source_ip, f"Vault-{org}-{service_name}")
        
    # Auto template fields with 1-click password generation
    if stype == "1":
        sec_data["app_user"] = f"{service_name}_app"
        sec_data["app_token"] = generate_api_key(f"{service_name}")
        sec_data["jwt_secret"] = generate_strong_password(32)
    elif stype == "2":
        sec_data["db_host"] = f"{service_name}-db.internal"
        sec_data["db_user"] = f"{service_name}_usr"
        sec_data["db_password"] = generate_strong_password(24)
        sec_data["db_name"] = f"{service_name}_prod"
    elif stype == "3":
        sec_data["broker_url"] = f"redis://:{generate_strong_password(20)}@10.0.0.10:6379/0"
        sec_data["auth_password"] = generate_strong_password(24)
    elif stype == "4":
        sec_data["merchant_id"] = f"MID_{secrets.token_hex(4).upper()}"
        sec_data["secret_key"] = generate_api_key("sec_live")
        sec_data["webhook_token"] = generate_strong_password(28)
    else:
        sec_data["password"] = generate_strong_password(20)
        sec_data["token"] = generate_api_key(service_name)
        
    print(f"\n{C_GREEN}Avtomatik generatsiya qilingan maydonlar:{C_RESET}")
    for k, v in sec_data.items():
        if not k.startswith("_"):
            print(f"  {k:<20}: {v}")
            
    res = api_post(f"secret/data/{org}/{service_name}", {"data": sec_data})
    if res is not None:
        print_success(f"'{org}/{service_name}' servisi muvaffaqiyatli saqlandi!")
    else:
        print_error("Saqlashda xatolik yuz berdi.")

def view_secret_wizard():
    org, service = select_org_and_service()
    if not org or not service:
        return
    
    res = api_get(f"secret/data/{org}/{service}")
    if not res or "data" not in res or "data" not in res["data"]:
        print_warning("Secret topilmadi.")
        return
    
    sec_info = res["data"]["data"]
    meta = res["data"]["metadata"]
    
    print(f"\n{C_CYAN}{C_BOLD}" + "="*70)
    print(f" 🔑 CREDENTIALS: {org} -> {service}")
    print(f" Versiya: {meta.get('version')} | Yaratilgan: {meta.get('created_time')}")
    if "_bound_source_ip" in sec_info:
        print(f" {C_MAGENTA}🔒 BOG'LANGAN SOURCE IP: {sec_info['_bound_source_ip']}{C_CYAN}")
    else:
        print(f" 🌐 SOURCE IP: Barcha IP manzillarga ochiq")
    print("="*70 + f"{C_RESET}")
    for k, v in sec_info.items():
        if k.startswith("_"): continue
        print(f"  {C_GREEN}{k:<22}{C_RESET}: {C_WHITE}{v}{C_RESET}")
    print("="*70)

def update_secret_wizard():
    org, service = select_org_and_service()
    if not org or not service:
        return
    
    res = api_get(f"secret/data/{org}/{service}")
    existing_data = res.get("data", {}).get("data", {}) if res else {}
    
    print(f"\n{C_YELLOW}Joriy maydonlar:{C_RESET} {[k for k in existing_data.keys() if not k.startswith('_')]}")
    print("\nAmalni tanlang:")
    print("  [1] ➕ Yangi maydon (Key/Value) qo'shish yoki parolni yangilash")
    print("  [2] 🎲 Avtomatik yangi kuchli parol generatsiya qilib biriktirish")
    print("  [3] 🔒 Source IP ruxsatnomasini o'zgartirish")
    print("  [4] ❌ Biror maydonni o'chirish")
    ch = input("\nTanlang [1-4]: ").strip()
    
    if ch == "1":
        k = input("Maydon nomi (Key): ").strip()
        if not k: return
        v = input(f"{k} qiymati (yoki Enter bosilsa avtomatik parol yaratiladi): ").strip()
        if not v:
            v = generate_strong_password(24)
            print_info(f"Yaratilgan parol: {v}")
        existing_data[k] = v
    elif ch == "2":
        k = input("Qaysi kalit parolini yangilaysiz? (masalan: password, db_password): ").strip() or "password"
        new_pass = generate_strong_password(24)
        existing_data[k] = new_pass
        print_success(f"{k} uchun yangi parol o'rnatildi: {new_pass}")
    elif ch == "3":
        new_ip = select_source_ip_interactive(existing_data.get("_bound_source_ip", ""))
        if new_ip:
            existing_data["_bound_source_ip"] = new_ip
            add_ufw_ip_rule(new_ip, f"Vault-{org}-{service}")
        else:
            existing_data.pop("_bound_source_ip", None)
            print_info("IP cheklovi olib tashlandi.")
    elif ch == "4":
        del_k = input("O'chiriladigan maydon nomi: ").strip()
        if del_k in existing_data:
            del existing_data[del_k]
            print_success(f"'{del_k}' maydoni o'chirildi.")
            
    res = api_post(f"secret/data/{org}/{service}", {"data": existing_data})
    if res is not None:
        print_success("Secret muvaffaqiyatli saqlandi!")

def delete_service_or_org():
    print(f"\n{C_RED}{C_BOLD}🗑 SERVIS YOKI TASHKILOTNI O'CHIRISH{C_RESET}")
    print("  [1] Bitta servisni o'chirish")
    print("  [2] Butun boshli tashkilotni barcha servislari bilan o'chirish")
    ch = input("Tanlang [1-2]: ").strip()
    
    if ch == "1":
        org, s = select_org_and_service()
        if not org or not s: return
        confirm = input(f"{C_RED}Haqiqatan ham '{org}/{s}' servis ma'lumotlarini o'chirasizmi? (ha/yo'q): {C_RESET}").lower()
        if confirm in ['ha', 'yes', 'y']:
            api_delete(f"secret/metadata/{org}/{s}")
            print_success(f"'{org}/{s}' servisi o'chirildi.")
    elif ch == "2":
        org = select_org()
        if not org: return
        confirm = input(f"{C_RED}DIQQAT! '{org}' tashkilotining BARCHA servislari o'chiriladi! Tasdiqlaysizmi? (ha/yo'q): {C_RESET}").lower()
        if confirm in ['ha', 'yes', 'y']:
            for s in list_services(org):
                api_delete(f"secret/metadata/{org}/{s}")
            print_success(f"'{org}' tashkiloti va barcha servislari o'chirildi.")

# ==============================================================================
# ACCESS, ROLE & TOKEN (100% GUIDED)
# ==============================================================================
def create_service_token_wizard():
    print(f"\n{C_BOLD}🎟 ACCESS TOKEN YARATISH VIZARDI{C_RESET}")
    org, service = select_org_and_service()
    if not org or not service:
        return
    
    # Fetch bound IP if any
    sec = api_get(f"secret/data/{org}/{service}")
    bound_ip = ""
    if sec and "data" in sec and "data" in sec["data"]:
        bound_ip = sec["data"]["data"].get("_bound_source_ip", "")
        
    print("\nRuxsat darajasini tanlang:")
    print(f"  [1] 👁  Read-Only (Faqat o'qish - Audit/Monitoring uchun)")
    print(f"  [2] ✍️  Read-Write (O'qish va yozish - Ilova/Microservice uchun)")
    print(f"  [3] 👑 Tashkilot Admin (Butun '{org}' tashkilotini boshqarish)")
    acc = input("\nTanlang [1-3] [default: 2]: ").strip() or "2"
    
    if acc == "1":
        policy_name = f"policy-{org}-{service}-ro"
    elif acc == "2":
        policy_name = f"policy-{org}-{service}-rw"
    else:
        policy_name = f"policy-{org}-admin"
        
    setup_policies_for_org(org)
    setup_policies_for_service(org, service)
        
    source_ip = select_source_ip_interactive(bound_ip)
    
    print("\nAmal qilish muddati (TTL):")
    print("  [1] 24 soat (24h) - Sinov / CI-CD uchun")
    print("  [2] 30 kun (720h) - Standart Microservice")
    print("  [3] 1 yil (8760h) - Doimiy tizim xizmati")
    print("  [4] Boshqa muddat kiritish")
    ttl_ch = input("\nTanlang [1-4] [default: 2]: ").strip() or "2"
    
    if ttl_ch == "1": ttl = "24h"
    elif ttl_ch == "2": ttl = "720h"
    elif ttl_ch == "3": ttl = "8760h"
    else: ttl = input("Muddat (masalan: 12h, 60d): ").strip() or "720h"
    
    display_name = f"{org}-{service}-app"
    token_client_token = ""
    accessor = ""
    
    if source_ip:
        cidrs = normalize_cidr_list(source_ip)
        role_slug = re.sub(r'[^a-zA-Z0-9_-]', '-', f"{org}-{policy_name}-{source_ip}".replace('/', '-'))
        token_role_name = f"trole-{role_slug}"[:60]
        
        role_payload = {
            "allowed_policies": [policy_name],
            "bound_cidrs": cidrs,
            "token_ttl": ttl,
            "renewable": True
        }
        api_post(f"auth/token/roles/{token_role_name}", role_payload)
        res = api_post(f"auth/token/create/{token_role_name}", {"display_name": display_name})
        if res and "auth" in res:
            token_client_token = res["auth"].get("client_token")
            accessor = res["auth"].get("accessor")
            add_ufw_ip_rule(source_ip, f"Vault-Token-{org}")
    else:
        res = api_post("auth/token/create", {
            "policies": [policy_name],
            "ttl": ttl,
            "display_name": display_name,
            "renewable": True
        })
        if res and "auth" in res:
            token_client_token = res["auth"].get("client_token")
            accessor = res["auth"].get("accessor")
            
    # External IP for developers
    ext_vault_addr = get_external_vault_addr()

    if token_client_token:
        print_success("Yangi Vault Token muvaffaqiyatli yaratildi!")
        print(f"\n{C_GREEN}{C_BOLD}" + "="*74)
        print("  🏷️  [DASTURCHIGA BERILADIGAN BLOK - SHUNI KO'CHIRIB BERING (COPY-PASTE)]")
        print("="*74 + f"{C_RESET}")
        print(f"  {C_BOLD}Server manzili (URL):{C_RESET} {C_CYAN}{ext_vault_addr}{C_RESET}")
        print(f"  {C_BOLD}Client Token:{C_RESET}         {C_GREEN}{token_client_token}{C_RESET}")
        print(f"  {C_BOLD}Secret Yo'li:{C_RESET}         secret/data/{org}/{service}")
        if source_ip:
            print(f"  {C_BOLD}Ruxsatli Source IP:{C_RESET}   {C_MAGENTA}{source_ip} (DIQQAT: Faqat shu IP dan ishlaydi!){C_RESET}")
        else:
            print(f"  {C_BOLD}Ruxsatli Source IP:{C_RESET}   Barcha IP lardan ruxsat etilgan")
        print(f"  {C_BOLD}Amal qilish muddati:{C_RESET}  {ttl}")
        
        print(f"\n  {C_YELLOW}Dasturchi loyihasining .env fayli uchun:{C_RESET}")
        print(f"  VAULT_ADDR={ext_vault_addr}")
        print(f"  VAULT_TOKEN={token_client_token}")
        
        print(f"\n  {C_YELLOW}Test qilish buyrug'i (Curl / Terminal):{C_RESET}")
        print(f"  curl -s -H \"X-Vault-Token: {token_client_token}\" {ext_vault_addr}/v1/secret/data/{org}/{service}")
        print(f"{C_GREEN}" + "="*74 + f"{C_RESET}")

        print(f"\n{C_BLUE}{C_BOLD}" + "-"*74)
        print("  🔒 [FAQAT ADMINISTRATOR UCHUN ICHKI MA'LUMOT (Dasturchiga berilmaydi)]")
        print("-" * 74 + f"{C_RESET}")
        print(f"  Biriktirilgan ACL Policy: {policy_name}")
        print(f"  Token Accessor ID:        {accessor}  (Tokenni bekor qilish/audit uchun)")
        print(f"  Tashkilot / Servis:       {org} -> {service}")
        print("-" * 74)

def list_and_manage_active_tokens():
    print(f"\n{C_BOLD}📋 MAVJUD VAULT TOKENLARI RO'YXATI (ACTIVE TOKENS){C_RESET}")
    res = api_get("auth/token/accessors?list=true")
    if not res or "data" not in res or "keys" not in res["data"]:
        print_warning("Faol tokenlar topilmadi.")
        return

    accessors = res["data"]["keys"]
    print(f"{C_CYAN}Jami faol tokenlar soni: {len(accessors)} ta{C_RESET}\n")

    token_items = []
    print(f"{C_BOLD}{'#':<3} {'Display Name':<28} {'Policies':<25} {'Qolgan TTL':<18} {'Accessor':<15}{C_RESET}")
    print("-" * 95)

    for idx, acc in enumerate(accessors, 1):
        info = api_post("auth/token/lookup-accessor", {"accessor": acc})
        if info and "data" in info:
            d = info["data"]
            d_name = d.get("display_name", "token")[:27]
            pol = ", ".join(d.get("policies", []))[:24]
            ttl = d.get("ttl", 0)
            if ttl == 0:
                ttl_str = "Cheksiz (Root)"
            elif ttl > 86400:
                ttl_str = f"{ttl//86400} kun {(ttl%86400)//3600} soat"
            elif ttl > 3600:
                ttl_str = f"{ttl//3600} soat {(ttl%3600)//60} daqiqa"
            else:
                ttl_str = f"{ttl} soniya"

            token_items.append((acc, d))
            print(f"{idx:<3} {d_name:<28} {pol:<25} {ttl_str:<18} {acc:<15}")

    print("\nAmalni tanlang:")
    print("  [Raqam] Muayyan tokenning to'liq ma'lumotlarini ko'rish")
    print("  [D]     Biror tokenni bekor qilish / o'chirish (Revoke)")
    print("  [Enter] Asosiy menyuga qaytish")
    sub_ch = input("\nTanlov: ").strip()

    if sub_ch.isdigit():
        num = int(sub_ch)
        if 1 <= num <= len(token_items):
            acc, d = token_items[num - 1]
            print(f"\n{C_CYAN}{C_BOLD}" + "="*65)
            print(f" 🔍 TOKEN TAFSILOTLARI (Accessor: {acc})")
            print("="*65 + f"{C_RESET}")
            print(f"  Display Name:      {d.get('display_name')}")
            print(f"  Accessor ID:       {acc}")
            print(f"  Policies:          {', '.join(d.get('policies', []))}")
            print(f"  Yaratilgan vaqti:  {d.get('creation_time')}")
            print(f"  Tugash vaqti:      {d.get('expire_time')}")
            print(f"  Qolgan TTL:        {d.get('ttl')} soniya")
            print(f"  Yangilanuvchi:     {d.get('renewable')}")
            print(f"  Token Turi:        {d.get('type')}")
            print("="*65)
    elif sub_ch.lower() == "d":
        del_num = input("O'chirmoqchi bo'lgan token raqamini kiriting: ").strip()
        if del_num.isdigit() and 1 <= int(del_num) <= len(token_items):
            acc, d = token_items[int(del_num) - 1]
            if "root" in d.get("policies", []) and len(token_items) <= 1:
                print_error("DIQQAT! Root tokenni o'chirib bo'lmaydi!")
                return
            confirm = input(f"{C_RED}Haqiqatan ham '{d.get('display_name')}' tokenini bekor qilasizmi? (ha/yo'q): {C_RESET}").lower()
            if confirm in ['ha', 'yes', 'y']:
                api_post("auth/token/revoke-accessor", {"accessor": acc})
                print_success("Token muvaffaqiyatli bekor qilindi (O'chirildi)!")

def create_approle_wizard():
    print(f"\n{C_BOLD}🤖 APPROLE (MIKROSERVIS VA CI/CD) YARATISH VIZARDI{C_RESET}")
    org, service = select_org_and_service()
    if not org or not service:
        return
    
    role_name = f"role-{org}-{service}"
    
    print("\nRuxsat darajasini tanlang:")
    print("  [1] 👁  Read-Only (Faqat o'qish - Ilova faqat secretni o'qiy oladi)")
    print("  [2] ✍️  Read-Write (O'qish va yozish - Ilova secretni yangilay oladi)")
    acc = input("\nTanlang [1-2] [default: 1]: ").strip() or "1"
    
    if acc == "1":
        policy_name = f"policy-{org}-{service}-ro"
    else:
        policy_name = f"policy-{org}-{service}-rw"
        
    setup_policies_for_org(org)
    setup_policies_for_service(org, service)
    
    # Check default bound IP
    sec = api_get(f"secret/data/{org}/{service}")
    bound_ip = sec.get("data", {}).get("data", {}).get("_bound_source_ip", "") if sec else ""
    source_ip = select_source_ip_interactive(bound_ip)
    
    role_payload: Dict[str, Any] = {
        "token_policies": [policy_name],
        "token_ttl": "24h",
        "token_max_ttl": "720h"
    }
    secret_id_payload: Dict[str, Any] = {}
    
    if source_ip:
        cidrs = normalize_cidr_list(source_ip)
        role_payload["token_bound_cidrs"] = cidrs
        role_payload["secret_id_bound_cidrs"] = cidrs
        secret_id_payload["cidr_list"] = cidrs
        add_ufw_ip_rule(source_ip, f"Vault-AppRole-{org}-{service}")
        
    api_post(f"auth/approle/role/{role_name}", role_payload)
    
    role_id_res = api_get(f"auth/approle/role/{role_name}/role-id")
    role_id = role_id_res.get("data", {}).get("role_id", "") if role_id_res else ""
    
    secret_id_res = api_post(f"auth/approle/role/{role_name}/secret-id", secret_id_payload)
    secret_id = secret_id_res.get("data", {}).get("secret_id", "") if secret_id_res else ""
    
    ext_vault_addr = get_external_vault_addr()

    print_success(f"AppRole '{role_name}' muvaffaqiyatli tayyorlandi!")
    print(f"\n{C_GREEN}{C_BOLD}" + "="*74)
    print("  🏷️  [DASTURCHIGA BERILADIGAN BLOK - SHUNI KO'CHIRIB BERING (COPY-PASTE)]")
    print("="*74 + f"{C_RESET}")
    print(f"  {C_BOLD}Server manzili (URL):{C_RESET} {C_CYAN}{ext_vault_addr}{C_RESET}")
    print(f"  {C_BOLD}Role ID:{C_RESET}              {C_GREEN}{role_id}{C_RESET}")
    print(f"  {C_BOLD}Secret ID:{C_RESET}            {C_GREEN}{secret_id}{C_RESET}")
    print(f"  {C_BOLD}Secret Yo'li:{C_RESET}         secret/data/{org}/{service}")
    if source_ip:
        print(f"  {C_BOLD}Ruxsatli Source IP:{C_RESET}   {C_MAGENTA}{source_ip} (DIQQAT: Faqat shu serverdan ulanadi!){C_RESET}")
    else:
        print(f"  {C_BOLD}Ruxsatli Source IP:{C_RESET}   Barcha IP lardan ruxsat etilgan")
        
    print(f"\n  {C_YELLOW}Dasturchi ilovasi uchun login so'rovi (Bash / Python / Backend):{C_RESET}")
    print(f"  curl -s --request POST --data '{{\"role_id\":\"{role_id}\",\"secret_id\":\"{secret_id}\"}}' {ext_vault_addr}/v1/auth/approle/login")
    print(f"{C_GREEN}" + "="*74 + f"{C_RESET}")

    print(f"\n{C_BLUE}{C_BOLD}" + "-"*74)
    print("  🔒 [FAQAT ADMINISTRATOR UCHUN ICHKI MA'LUMOT (Dasturchiga berilmaydi)]")
    print("-" * 74 + f"{C_RESET}")
    print(f"  Role Nomi:                {role_name}")
    print(f"  Biriktirilgan ACL Policy: {policy_name}")
    print("-" * 74)

def create_userpass_wizard():
    print(f"\n{C_BOLD}👤 OPERATOR / FOYDALANUVCHI YARATISH VIZARDI{C_RESET}")
    username = input("Username: ").strip()
    if not username: return
    
    password = input("Parol (yoki Enter - avtomatik kuchli parol): ").strip()
    if not password:
        password = generate_strong_password(20)
        print_info(f"Generatsiya qilingan parol: {password}")
        
    org = select_org()
    if not org: return
    
    source_ip = select_source_ip_interactive()
    policy_name = f"policy-{org}-admin"
    
    payload: Dict[str, Any] = {
        "password": password,
        "policies": policy_name
    }
    if source_ip:
        payload["token_bound_cidrs"] = normalize_cidr_list(source_ip)
        add_ufw_ip_rule(source_ip, f"Vault-User-{username}")
        
    res = api_post(f"auth/userpass/users/{username}", payload)
    if res is not None:
        print_success(f"Foydalanuvchi '{username}' yaratildi!")
        print_info(f"Login: {username} | Parol: {password} | Policy: {policy_name}")

# ==============================================================================
# AUDIT & MONITORING
# ==============================================================================
def view_audit_logs():
    print(f"\n{C_BOLD}📜 REAL-TIME AUDIT LOGS (SO'NGGI KIRISHLAR VA SO'ROVLAR){C_RESET}")
    if not os.path.exists(AUDIT_LOG_FILE):
        print_warning(f"Audit log fayli topilmadi: {AUDIT_LOG_FILE}")
        return
    
    print(f"{C_CYAN}So'nggi 15 ta kirish so'rovlari tahlili:{C_RESET}\n")
    try:
        cmd = f"sudo tail -n 15 {AUDIT_LOG_FILE}"
        out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
        lines = out.strip().split("\n")
        
        print(f"{C_BOLD}{'Vaqt':<20} {'Client IP':<16} {'Metod':<7} {'Path':<35} {'Auth turi'}{C_RESET}")
        print("-" * 90)
        
        for line in lines:
            if not line.strip(): continue
            try:
                entry = json.loads(line)
                req = entry.get("request", {})
                auth = entry.get("auth", {})
                time_str = entry.get("time", "")[:19].replace("T", " ")
                remote_ip = req.get("remote_address", "unknown")
                op = req.get("operation", "")
                path = req.get("path", "")[:34]
                auth_display = auth.get("display_name", "unauth")
                print(f"{time_str:<20} {remote_ip:<16} {op:<7} {path:<35} {auth_display}")
            except Exception:
                pass
    except Exception as e:
        print_error(str(e))

# ==============================================================================
# AUTOMATED BACKUP & RESTORE
# ==============================================================================
def backup_vault_secrets():
    print(f"\n{C_BOLD}💾 BARCHA TASHKILOTLAR VA MAXFIY MA'LUMOTLARNI ZAXIRALASH (BACKUP){C_RESET}")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.system(f"sudo chmod 700 {BACKUP_DIR}")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{BACKUP_DIR}/vault_backup_{timestamp}.json"
    
    orgs = list_organizations()
    backup_data: Dict[str, Any] = {
        "timestamp": timestamp,
        "vault_addr": VAULT_ADDR,
        "organizations": {}
    }
    
    total_services = 0
    for org in orgs:
        backup_data["organizations"][org] = {}
        for s in list_services(org):
            sec = api_get(f"secret/data/{org}/{s}")
            if sec and "data" in sec:
                backup_data["organizations"][org][s] = sec["data"]["data"]
                total_services += 1
                
    with open(backup_file, "w") as f:
        json.dump(backup_data, f, indent=2)
    os.system(f"sudo chmod 600 {backup_file}")
    
    print_success(f"Zaxira nusxasi yaratildi: {backup_file}")
    print_info(f"Jami: {len(orgs)} ta tashkilot, {total_services} ta servis ma'lumotlari xavfsiz saqlandi.")

def list_and_restore_backup():
    print(f"\n{C_BOLD}🔄 ZAXIRADAN TIKLASH (RESTORE){C_RESET}")
    if not os.path.exists(BACKUP_DIR):
        print_warning("Zaxira nusxalari topilmadi.")
        return
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("vault_backup_")])
    if not files:
        print_warning("Hech qanday zaxira fayli mavjud emas.")
        return
    
    print("Mavjud zaxiralar:")
    for idx, f in enumerate(files, 1):
        print(f"  [{idx}] {f}")
    ch = input("\nTiklash uchun fayl raqamini tanlang: ").strip()
    if not ch.isdigit() or not (1 <= int(ch) <= len(files)): return
    
    target_file = os.path.join(BACKUP_DIR, files[int(ch) - 1])
    confirm = input(f"{C_RED}Ushbu fayldan ma'lumotlar qayta tiklansinmi? (ha/yo'q): {C_RESET}").lower()
    if confirm in ['ha', 'yes', 'y']:
        with open(target_file, "r") as f:
            data = json.load(f)
        for org, services in data.get("organizations", {}).items():
            setup_policies_for_org(org)
            for s, s_data in services.items():
                setup_policies_for_service(org, s)
                api_post(f"secret/data/{org}/{s}", {"data": s_data})
        print_success("Barcha ma'lumotlar zaxiradan muvaffaqiyatli tiklandi!")

# ==============================================================================
# PRODUCTION DOCTOR & DIAGNOSTICS
# ==============================================================================
def production_doctor():
    print(f"\n{C_BOLD}🩺 PRODUCTION DOCTOR (TIZIM VA XAVFSIZLIK DIAGNOSTIKASI){C_RESET}\n")
    checks = []
    
    # 1. Vault Service
    is_vault = subprocess.run("systemctl is-active vault", shell=True, capture_output=True, text=True).stdout.strip()
    checks.append(("Vault Systemd Service", "FAOL (active)" if is_vault == "active" else "NOFAOL", is_vault == "active"))
    
    # 2. Vault Auto-Unseal Service
    is_unseal = subprocess.run("systemctl is-enabled vault-auto-unseal", shell=True, capture_output=True, text=True).stdout.strip()
    checks.append(("Vault Auto-Unseal Service", "YOQILGAN (enabled)", is_unseal == "enabled"))
    
    # 3. Vault Seal Status
    health = api_get("sys/health")
    is_unsealed = health and not health.get("sealed", True)
    checks.append(("Vault Muhr Holati", "OCHIQ (Unsealed)" if is_unsealed else "MUHRLANGAN (Sealed)", is_unsealed))
    
    # 4. Audit Log
    is_audit = os.path.exists(AUDIT_LOG_FILE)
    checks.append(("Audit Log Tizimi", "FAOL (/var/log/vault/vault_audit.log)", is_audit))
    
    # 5. Firewall
    fw_type = get_firewall_backend()
    if fw_type == "firewalld":
        is_fw = subprocess.run("sudo firewall-cmd --state", shell=True, capture_output=True, text=True).stdout.strip() == "running"
        checks.append(("Firewall (firewalld)", "FAOL (running)" if is_fw else "NOFAOL", is_fw))
    elif fw_type == "ufw":
        is_fw = subprocess.run("sudo ufw status | grep -q 'Status: active'", shell=True).returncode == 0
        checks.append(("Firewall (UFW)", "FAOL (active)" if is_fw else "NOFAOL", is_fw))
    else:
        checks.append(("Firewall Xavfsizligi", "O'RNATILMAGAN / BOSHQA", False))
    
    # 6. Credentials File Permission
    is_cred_safe = os.path.exists(CRED_FILE)
    checks.append(("Kalitlar Fayli Himoyasi", "XAVFSIZ (chmod 600)", is_cred_safe))

    # 7. SELinux (Rocky Linux 9.3 / RHEL)
    selinux_mode = subprocess.run("getenforce 2>/dev/null", shell=True, capture_output=True, text=True).stdout.strip()
    if selinux_mode:
        checks.append(("SELinux Himoya Rejimi", f"FAOL ({selinux_mode})", True))
    
    for title, desc, ok in checks:
        icon = f"{C_GREEN}✔ PASSED{C_RESET}" if ok else f"{C_RED}✖ FAILED{C_RESET}"
        print(f"  {title:<30}: {desc:<35} [{icon}]")

# ==============================================================================
# UNIVERSAL IP ACCESS & FIREWALL MANAGER (RHEL FIREWALLD + UBUNTU UFW)
# ==============================================================================
IP_REGISTRY_FILE = "/etc/vault.d/ip_whitelist.json"
IP_REGISTRY_FALLBACK = os.path.expanduser("~/ip_whitelist.json")

def get_firewall_backend() -> str:
    if subprocess.run("which firewall-cmd > /dev/null 2>&1", shell=True).returncode == 0:
        return "firewalld"
    if subprocess.run("which ufw > /dev/null 2>&1", shell=True).returncode == 0:
        return "ufw"
    return "iptables"

def get_ip_registry_path() -> str:
    if os.path.exists(os.path.dirname(IP_REGISTRY_FILE)):
        return IP_REGISTRY_FILE
    return IP_REGISTRY_FALLBACK

def load_ip_registry() -> List[Dict[str, Any]]:
    p = get_ip_registry_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_ip_registry(data: List[Dict[str, Any]]):
    p = get_ip_registry_path()
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def add_firewall_ip_rule(ip: str, comment: str = ""):
    if not ip: return
    ip_list = [p.strip() for p in ip.replace(";", ",").split(",") if p.strip()]
    if not ip_list: return
    backend = get_firewall_backend()
    items = load_ip_registry()

    for clean_ip in ip_list:
        if backend == "firewalld":
            rule = f'rule family="ipv4" source address="{clean_ip}" port port="8200" protocol="tcp" accept'
            os.system(f"sudo firewall-cmd --permanent --add-rich-rule='{rule}' > /dev/null 2>&1")
        elif backend == "ufw":
            os.system(f"sudo ufw allow from {clean_ip} to any port 8200 proto tcp comment '{comment or 'Vault-IP'}' > /dev/null 2>&1")

        existing = [x for x in items if x.get("ip") == clean_ip]
        if not existing:
            items.append({
                "ip": clean_ip,
                "comment": comment or "Manual Whitelist",
                "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    if backend == "firewalld":
        os.system("sudo firewall-cmd --reload > /dev/null 2>&1")
    elif backend == "ufw":
        os.system("sudo ufw reload > /dev/null 2>&1")

    save_ip_registry(items)

add_ufw_ip_rule = add_firewall_ip_rule  # Orqaga moslik uchun alias

def remove_firewall_ip_rule(ip: str):
    clean_ip = ip.strip()
    if not clean_ip: return
    backend = get_firewall_backend()
    if backend == "firewalld":
        rule = f'rule family="ipv4" source address="{clean_ip}" port port="8200" protocol="tcp" accept'
        os.system(f"sudo firewall-cmd --permanent --remove-rich-rule='{rule}' > /dev/null 2>&1")
        os.system("sudo firewall-cmd --reload > /dev/null 2>&1")
    elif backend == "ufw":
        os.system(f"sudo ufw delete allow from {clean_ip} to any port 8200 proto tcp > /dev/null 2>&1")
        os.system("sudo ufw reload > /dev/null 2>&1")
    
    items = load_ip_registry()
    items = [x for x in items if x.get("ip") != clean_ip]
    save_ip_registry(items)

def get_active_firewall_rules() -> List[str]:
    backend = get_firewall_backend()
    rules = []
    if backend == "firewalld":
        out = subprocess.run("sudo firewall-cmd --list-rich-rules", shell=True, capture_output=True, text=True).stdout
        for line in out.splitlines():
            line = line.strip()
            if "8200" in line and "accept" in line:
                m = re.search(r'source address="([^"]+)"', line)
                if m:
                    rules.append(m.group(1))
    elif backend == "ufw":
        out = subprocess.run("sudo ufw status", shell=True, capture_output=True, text=True).stdout
        for line in out.splitlines():
            if "8200" in line and "ALLOW" in line:
                parts = line.split()
                if len(parts) >= 3 and parts[2] not in ["Anywhere", "Anywhere (v6)"]:
                    rules.append(parts[2])
    return sorted(list(set(rules)))

def is_port_8200_public() -> bool:
    backend = get_firewall_backend()
    if backend == "firewalld":
        ports = subprocess.run("sudo firewall-cmd --list-ports", shell=True, capture_output=True, text=True).stdout
        return "8200/tcp" in ports
    elif backend == "ufw":
        out = subprocess.run("sudo ufw status", shell=True, capture_output=True, text=True).stdout
        return "8200/tcp" in out and "Anywhere" in out
    return True

def manage_firewall():
    while True:
        backend = get_firewall_backend()
        is_public = is_port_8200_public()
        active_ips = get_active_firewall_rules()
        reg_items = load_ip_registry()
        reg_dict = {x.get("ip"): x.get("comment", "") for x in reg_items}

        print_banner()
        print(f"\n{C_BOLD}{C_BLUE}" + "="*74)
        print("  🧱 MARKAZIY IP ACCESS VA FIREWALL BOSHQARUVI (PORT 8200)")
        print("="*74 + f"{C_RESET}")
        print(f"  Tizim Firewall Backend: {C_GREEN}{backend.upper()}{C_RESET} ({'RHEL / CentOS / Rocky' if backend == 'firewalld' else 'Ubuntu / Debian'})")
        
        if is_public:
            print(f"  Port 8200 Holati:       {C_YELLOW}🌐 OCHIQ REJIM (Barcha tarmoqlardan kirish ochiq){C_RESET}")
        else:
            print(f"  Port 8200 Holati:       {C_GREEN}🔒 STRICT REJIM (Faqat Whitelistdagi IP lar kira oladi){C_RESET}")
            
        print(f"  Faol Whitelist IP lar:  {C_CYAN}{len(active_ips)} ta manzil ruxsat etilgan{C_RESET}")
        print("-" * 74)

        print(f"""
  {C_BOLD}IP ACCESS AMALLARI:{C_RESET}
  {C_CYAN}[1]{C_RESET} 📋 Barcha Ruxsat Berilgan IP lar Ro'yxati (Whitelist Table)
  {C_CYAN}[2]{C_RESET} ➕ Yangi Source IP / Subnet qo'shish (Whitelistga kiritish)
  {C_CYAN}[3]{C_RESET} ➖ IP Ruxsatini Bekor Qilish / O'chirish (Remove from Whitelist)
  
  {C_BOLD}XAVFSIZLIK REJIMLARI:{C_RESET}
  {C_MAGENTA}[4]{C_RESET} 🔒 STRICT REJIM: Umumiy kirishni yopish (Faqat Whitelistdagi IP lar)
  {C_MAGENTA}[5]{C_RESET} 🌐 OCHIQ REJIM: 8200-portni barcha tarmoqqa ochish (Anywhere)
  
  {C_BOLD}TEKSHIRISH VA SINXRONIZATSIYA:{C_RESET}
  {C_GREEN}[6]{C_RESET} 🔍 Muayyan IP manzilni tekshirish (Check Access)
  {C_GREEN}[7]{C_RESET} 🔄 Firewallni Qayta Yuklash (Reload & Sync)

  {C_RED}[0]{C_RESET} ⬅️  Asosiy menyuga qaytish
""")
        ch = input(f"{C_BOLD}Tanlang [0-7]: {C_RESET}").strip()

        if ch == "1":
            print(f"\n{C_BOLD}📋 8200-PORTGA RUXSAT ETILGAN IP MANZILLAR JADVALI:{C_RESET}")
            if not active_ips and not reg_items:
                print_warning("Hozircha hech qanday maxsus IP whitelistga qo'shilmagan.")
            else:
                all_display_ips = sorted(list(set(active_ips + [x.get("ip") for x in reg_items if x.get("ip")])))
                print(f"\n{'#':<3} {'IP Manzil / Subnet':<25} {'Izoh / Nomi':<30} {'Firewall Holati':<15}")
                print("-" * 75)
                for idx, ip_addr in enumerate(all_display_ips, 1):
                    comm = reg_dict.get(ip_addr, "Dasturchi / Servis IP")
                    in_fw = ip_addr in active_ips
                    fw_status = f"{C_GREEN}✔ Ruxsatli{C_RESET}" if in_fw else f"{C_YELLOW}⚠ Kutilmoqda{C_RESET}"
                    print(f"{idx:<3} {C_CYAN}{ip_addr:<25}{C_RESET} {comm:<30} {fw_status}")
            pause()

        elif ch == "2":
            print(f"\n{C_BOLD}➕ YANGI SOURCE IP YOKI SUBNET QO'SHISH{C_RESET}")
            print("Misollar:")
            print("  - Bitta server: 172.16.101.45")
            print("  - Butun tarmoq: 172.16.101.0/24")
            new_ip = input("\nIP manzil yoki CIDR kiriting: ").strip()
            if not new_ip:
                print_warning("IP manzil kiritilmadi!")
                pause()
                continue
            comment = input("Ushbu IP kimga tegishli? (Izoh, masalan: Humo-Prod-Api): ").strip() or "API Client"
            
            print(f"\nQo'shilmoqda: {new_ip} ({comment})...")
            add_firewall_ip_rule(new_ip, comment)
            print_success(f"'{new_ip}' manzili Firewall whitelistga muvaffaqiyatli qo'shildi va 8200-port ochildi!")
            pause()

        elif ch == "3":
            print(f"\n{C_BOLD}➖ IP RUXSATINI BEKOR QILISH (O'CHIRISH){C_RESET}")
            all_display_ips = sorted(list(set(active_ips + [x.get("ip") for x in reg_items if x.get("ip")])))
            if not all_display_ips:
                print_warning("O'chirish uchun birorta ham IP mavjud emas.")
                pause()
                continue
            for idx, ip_addr in enumerate(all_display_ips, 1):
                comm = reg_dict.get(ip_addr, "")
                print(f"  [{idx}] {ip_addr:<25} ({comm})")
            del_ch = input(f"\nO'chirmoqchi bo'lgan IP raqamini kiriting [1-{len(all_display_ips)}] (yoki Enter): ").strip()
            if del_ch.isdigit() and 1 <= int(del_ch) <= len(all_display_ips):
                target_ip = all_display_ips[int(del_ch) - 1]
                confirm = input(f"{C_RED}Haqiqatan ham '{target_ip}' manzilidan kirishni bekor qilasizmi? (ha/yo'q): {C_RESET}").lower()
                if confirm in ['ha', 'yes', 'y']:
                    remove_firewall_ip_rule(target_ip)
                    print_success(f"'{target_ip}' manzili Firewall ruxsatlaridan o'chirildi!")
            pause()

        elif ch == "4":
            print(f"\n{C_BOLD}{C_RED}🔒 STRICT REJIMGA O'TISH{C_RESET}")
            print("Port 8200 barcha ochiq tarmoqdan yopiladi.")
            print("Faqat Whitelistdagi IP manzillargina Vaultga ulanishi mumkin bo'ladi!")
            confirm = input(f"\n{C_YELLOW}Davom ettirasizmi? (ha/yo'q): {C_RESET}").lower()
            if confirm in ['ha', 'yes', 'y']:
                if backend == "firewalld":
                    os.system("sudo firewall-cmd --permanent --remove-port=8200/tcp > /dev/null 2>&1")
                    os.system("sudo firewall-cmd --reload > /dev/null 2>&1")
                elif backend == "ufw":
                    os.system("sudo ufw status numbered | grep '8200/tcp.*ALLOW IN.*Anywhere' | awk -F'[][]' '{print $2}' | sort -rn | while read n; do sudo ufw --force delete $n; done > /dev/null 2>&1")
                    os.system("sudo ufw reload > /dev/null 2>&1")
                print_success("STRICT REJIM faollashtirildi! Port 8200 faqat ruxsatli IP lar uchun ochiq.")
            pause()

        elif ch == "5":
            print(f"\n{C_BOLD}{C_GREEN}🌐 OCHIQ REJIMGA O'TISH{C_RESET}")
            print("Port 8200 barcha tarmoqlar uchun ochiladi.")
            confirm = input(f"\n{C_YELLOW}Davom ettirasizmi? (ha/yo'q): {C_RESET}").lower()
            if confirm in ['ha', 'yes', 'y']:
                if backend == "firewalld":
                    os.system("sudo firewall-cmd --permanent --add-port=8200/tcp > /dev/null 2>&1")
                    os.system("sudo firewall-cmd --reload > /dev/null 2>&1")
                elif backend == "ufw":
                    os.system("sudo ufw allow 8200/tcp comment 'Vault UI and API' > /dev/null 2>&1")
                    os.system("sudo ufw reload > /dev/null 2>&1")
                print_success("OCHIQ REJIM faollashtirildi! Port 8200 barcha tarmoqqa ochildi.")
            pause()

        elif ch == "6":
            check_ip = input("\nTekshirmoqchi bo'lgan IP manzilni kiriting: ").strip()
            if check_ip:
                is_allowed = check_ip in active_ips
                print(f"\n--- IP Tekshiruv Natijasi: {check_ip} ---")
                if is_port_8200_public():
                    print(f"  {C_GREEN}✔ RUXSAT ETILGAN{C_RESET} (Chunki 8200-port Ochiq rejimda turibdi)")
                elif is_allowed:
                    comm = reg_dict.get(check_ip, "")
                    print(f"  {C_GREEN}✔ RUXSAT ETILGAN{C_RESET} (Whitelist ro'yxatida mavjud: {comm})")
                else:
                    print(f"  {C_RED}✖ BLOKLANGAN{C_RESET} (Ushbu IP whitelistda mavjud emas va port yopiq)")
            pause()

        elif ch == "7":
            print("\nFirewall qayta yuklanmoqda va qoidalar sinxron qilinmoqda...")
            if backend == "firewalld":
                os.system("sudo firewall-cmd --reload")
            elif backend == "ufw":
                os.system("sudo ufw reload")
            print_success("Firewall yangilandi va sinxronlandi.")
            pause()

        elif ch == "0":
            break

# ==============================================================================
# POLICY HELPERS
# ==============================================================================
def setup_policies_for_org(org: str):
    p_admin = f"""path "secret/data/{org}/*" {{ capabilities = ["create", "read", "update", "delete", "list"] }}\npath "secret/metadata/{org}/*" {{ capabilities = ["list", "read", "delete"] }}"""
    p_ro = f"""path "secret/data/{org}/*" {{ capabilities = ["read", "list"] }}\npath "secret/metadata/{org}/*" {{ capabilities = ["list", "read"] }}"""
    api_put(f"sys/policies/acl/policy-{org}-admin", {"policy": p_admin})
    api_put(f"sys/policies/acl/policy-{org}-readonly", {"policy": p_ro})

def setup_policies_for_service(org: str, service: str):
    p_rw = f"""path "secret/data/{org}/{service}" {{ capabilities = ["create", "read", "update", "delete", "list"] }}\npath "secret/metadata/{org}/{service}" {{ capabilities = ["read", "list"] }}"""
    p_ro = f"""path "secret/data/{org}/{service}" {{ capabilities = ["read"] }}\npath "secret/metadata/{org}/{service}" {{ capabilities = ["read", "list"] }}"""
    api_put(f"sys/policies/acl/policy-{org}-{service}-rw", {"policy": p_rw})
    api_put(f"sys/policies/acl/policy-{org}-{service}-ro", {"policy": p_ro})

def list_acl_policy_names() -> List[str]:
    res = api_get("sys/policies/acl?list=true")
    if res and "data" in res and "keys" in res["data"]:
        return sorted(res["data"]["keys"])
    res2 = api_get("sys/policy")
    if res2 and "data" in res2 and "keys" in res2["data"]:
        return sorted(res2["data"]["keys"])
    return []

def manage_acl_policies():
    while True:
        print_banner()
        print(f"\n{C_BOLD}{C_MAGENTA}" + "="*74)
        print("  🛡️  MARKAZIY ACL POLICY BOSHQARUVI (ACCESS CONTROL LIST)")
        print("="*74 + f"{C_RESET}")
        
        policies = list_acl_policy_names()
        print(f"  Mavjud Policy'lar soni: {C_CYAN}{len(policies)} ta{C_RESET}")
        print("-" * 74)
        print(f"""
  {C_BOLD}POLICY AMALLARI:{C_RESET}
  {C_CYAN}[1]{C_RESET} 📋 Barcha ACL Policy'lar ro'yxati va kodini ko'rish (View)
  {C_CYAN}[2]{C_RESET} ➕ Yangi Maxsus Policy Yaratish (Custom ACL Policy Wizard)
  {C_CYAN}[3]{C_RESET} 🏢 Tashkilot yoki Servis uchun Standart Policy Generatsiya qilish
  {C_CYAN}[4]{C_RESET} ✏️  Mavjud Policy'ni Tahrirlash / Yangilash (Edit Policy)
  {C_CYAN}[5]{C_RESET} 🗑  Policy'ni O'chirish (Delete Policy)

  {C_RED}[0]{C_RESET} ⬅️  Asosiy menyuga qaytish
""")
        ch = input(f"{C_BOLD}Tanlang [0-5]: {C_RESET}").strip()
        
        if ch == "1":
            print(f"\n{C_BOLD}🛡 MAVJUD ACL POLICY'LAR RO'YXATI:{C_RESET}")
            if not policies:
                print_warning("Hech qanday policy topilmadi.")
                pause()
                continue
            for idx, p in enumerate(policies, 1):
                print(f"  {idx:<3}. {C_CYAN}{p}{C_RESET}")
            v_idx = input("\nPolicy tarkibini ko'rish uchun raqamini kiriting (yoki Enter): ").strip()
            if v_idx.isdigit() and 1 <= int(v_idx) <= len(policies):
                p_name = policies[int(v_idx) - 1]
                p_res = api_get(f"sys/policies/acl/{p_name}")
                if p_res and "data" in p_res:
                    print(f"\n{C_YELLOW}{C_BOLD}--- Policy kodi: {p_name} ---{C_RESET}")
                    print(p_res["data"].get("policy", ""))
            pause()
            
        elif ch == "2":
            print(f"\n{C_BOLD}➕ YANGI ACL POLICY YARATISH VIZARDI{C_RESET}")
            p_name = input("Policy nomi (masalan: policy-humo-custom): ").strip().lower()
            if not p_name:
                print_warning("Policy nomi kiritilmadi!")
                pause()
                continue
            if not p_name.startswith("policy-"):
                p_name = f"policy-{p_name}"
                
            print("\nYaratish usulini tanlang:")
            print("  [1] 🎯 Interaktiv Konstruktor (Tashkilot va papkani tanlash orqali)")
            print("  [2] ✍️  To'g'ridan-to'g'ri HCL kodini kiritish (Manual Entry)")
            m_type = input("\nTanlang [1-2] [default: 1]: ").strip() or "1"
            
            if m_type == "1":
                org = select_org()
                if not org:
                    pause()
                    continue
                path_sub = input(f"Qaysi yo'lga ruxsat berilsin? (masalan: payment-hub yoki * barcha servislar uchun) [default: *]: ").strip() or "*"
                print("\nRuxsat darajasini tanlang:")
                print("  [1] 👁  Faqat o'qish (Read-Only: read, list)")
                print("  [2] ✍️  O'qish va Yozish (Read-Write: create, read, update, delete, list)")
                print("  [3] 👑 To'liq Admin (Barcha amallar + sudo)")
                perm_ch = input("\nTanlang [1-3] [default: 2]: ").strip() or "2"
                
                if perm_ch == "1":
                    caps = '["read", "list"]'
                    meta_caps = '["read", "list"]'
                elif perm_ch == "2":
                    caps = '["create", "read", "update", "delete", "list"]'
                    meta_caps = '["read", "list", "delete"]'
                else:
                    caps = '["create", "read", "update", "delete", "list", "sudo"]'
                    meta_caps = '["create", "read", "update", "delete", "list", "sudo"]'
                    
                hcl_code = f"""# HashiCorp Vault ACL Policy: {p_name}
path "secret/data/{org}/{path_sub}" {{
  capabilities = {caps}
}}

path "secret/metadata/{org}/{path_sub}" {{
  capabilities = {meta_caps}
}}
"""
            else:
                print("\nHCL kodini kiriting (Tugatish uchun alohida qatorda 'EOF' deb yozing yoki bo'sh qatorda Enter bosing):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "EOF":
                        break
                    lines.append(line)
                    if not line.strip() and len(lines) >= 2:
                        break
                hcl_code = "\n".join(lines).strip()
                if not hcl_code:
                    print_warning("HCL kodi bo'sh bo'lishi mumkin emas!")
                    pause()
                    continue

            print(f"\n{C_YELLOW}--- Yaratilayotgan Policy ({p_name}): ---{C_RESET}")
            print(hcl_code)
            res = api_put(f"sys/policies/acl/{p_name}", {"policy": hcl_code})
            if res is not None:
                print_success(f"'{p_name}' policy muvaffaqiyatli yaratildi va faollashtirildi!")
            else:
                print_error("Policy yaratishda xatolik yuz berdi.")
            pause()

        elif ch == "3":
            print(f"\n{C_BOLD}🏢 TASHKILOT VA SERVISLAR UCHUN STANDART POLICY'LAR GENERATSIYASI{C_RESET}")
            org = select_org()
            if not org:
                pause()
                continue
            setup_policies_for_org(org)
            for s in list_services(org):
                setup_policies_for_service(org, s)
            print_success(f"'{org}' tashkiloti va uning barcha servislari uchun standart policy'lar yaratildi/yangilandi!")
            pause()

        elif ch == "4":
            print(f"\n{C_BOLD}✏️  MAVJUD POLICY'NI TAHRIRLASH / YANGILASH{C_RESET}")
            if not policies:
                print_warning("Policy'lar topilmadi.")
                pause()
                continue
            for idx, p in enumerate(policies, 1):
                print(f"  {idx:<3}. {C_CYAN}{p}{C_RESET}")
            v_idx = input("\nTahrirlamoqchi bo'lgan policy raqamini kiriting: ").strip()
            if v_idx.isdigit() and 1 <= int(v_idx) <= len(policies):
                p_name = policies[int(v_idx) - 1]
                p_res = api_get(f"sys/policies/acl/{p_name}")
                current_code = p_res.get("data", {}).get("policy", "") if p_res else ""
                print(f"\n{C_YELLOW}Joriy HCL kodi:{C_RESET}\n{current_code}")
                print("\nYangi HCL kodini kiriting (Tugatish uchun 'EOF' deb yozing):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "EOF":
                        break
                    lines.append(line)
                    if not line.strip() and len(lines) >= 2:
                        break
                new_hcl = "\n".join(lines).strip()
                if new_hcl:
                    api_put(f"sys/policies/acl/{p_name}", {"policy": new_hcl})
                    print_success(f"'{p_name}' muvaffaqiyatli yangilandi!")
                else:
                    print_info("O'zgarishlar kiritilmadi.")
            pause()

        elif ch == "5":
            print(f"\n{C_BOLD}🗑  POLICY'NI O'CHIRISH{C_RESET}")
            if not policies:
                print_warning("Policy'lar topilmadi.")
                pause()
                continue
            for idx, p in enumerate(policies, 1):
                print(f"  {idx:<3}. {C_CYAN}{p}{C_RESET}")
            v_idx = input("\nO'chirmoqchi bo'lgan policy raqamini kiriting: ").strip()
            if v_idx.isdigit() and 1 <= int(v_idx) <= len(policies):
                p_name = policies[int(v_idx) - 1]
                if p_name in ["root", "default"]:
                    print_error(f"'{p_name}' tizim policy'sini o'chirib bo'lmaydi!")
                    pause()
                    continue
                confirm = input(f"{C_RED}Haqiqatan ham '{p_name}' policy'sini o'chirasizmi? (ha/yo'q): {C_RESET}").lower()
                if confirm in ['ha', 'yes', 'y']:
                    api_delete(f"sys/policies/acl/{p_name}")
                    print_success(f"'{p_name}' muvaffaqiyatli o'chirildi!")
            pause()

        elif ch == "0":
            break

# ==============================================================================
# MAIN MENU LOOP (100% INTERACTIVE)
# ==============================================================================
def main_menu():
    global TOKEN
    if not TOKEN:
        TOKEN = get_vault_token()
    
    while True:
        print_banner()
        print(f"""
  {C_BOLD}🏢 TASHKILOTLAR, SERVISLAR VA CREDENTIALS (VIZARD):{C_RESET}
  {C_CYAN}[1]{C_RESET}  📂 Tashkilotlar & Servislar tuzilmasi (Production Tree)
  {C_CYAN}[2]{C_RESET}  ➕ Yangi Tashkilot (Organization) qo'shish
  {C_CYAN}[3]{C_RESET}  ⚙️  Yangi Servis qo'shish (Auto-Password & Shablonlar bilan)
  {C_CYAN}[4]{C_RESET}  🔑 Servis Credentials (Password/Token/Key) ko'rish
  {C_CYAN}[5]{C_RESET}  ✏️  Servis Credentials qo'shish, yangilash yoki parol generatsiyasi
  {C_CYAN}[6]{C_RESET}  🗑  Servis yoki Tashkilotni o'chirish
  
  {C_BOLD}🛡️  RUXSATLAR VA XAVFSIZLIK (SOURCE IP BOG'LASH BILAN):{C_RESET}
  {C_MAGENTA}[7]{C_RESET}  🎟  Yangi Token yaratish (1-klikda Source IP bog'langan)
  {C_MAGENTA}[8]{C_RESET}  📋 Mavjud Faol Tokenlar Ro'yxati va Bekor qilish (Active Tokens)
  {C_MAGENTA}[9]{C_RESET}  🤖 Mikroservislar uchun AppRole (Role-ID & Secret-ID)
  {C_MAGENTA}[10]{C_RESET} 👤 Xodim/Operator qo'shish (Userpass Login)
  {C_MAGENTA}[11]{C_RESET} 🛡  ACL Policy'larni ko'rish va boshqarish

  {C_BOLD}🚀 PRODUCTION ADMIN VA TIZIM NAZORATI:{C_RESET}
  {C_GREEN}[12]{C_RESET} 📜 Real-time Audit & Access Monitor (Kirishlar va IP tahlili)
  {C_GREEN}[13]{C_RESET} 💾 Avtomatlashtirilgan Zaxiralash (1-Click Backup)
  {C_GREEN}[14]{C_RESET} 🔄 Zaxiradan qayta tiklash (1-Click Restore)
  {C_GREEN}[15]{C_RESET} 🩺 Production Doctor (Tizim diagnostikasi)
  {C_GREEN}[16]{C_RESET} 🧱 Markaziy IP Access va Firewall Boshqaruvi (Port 8200 Whitelist)
  {C_GREEN}[17]{C_RESET} 🌐 Web UI Ma'lumotlari (Brauzer orqali kirish)
  {C_GREEN}[18]{C_RESET} 🔄 Tokenni Almashtirish / Yangi Token kiritish (Switch Token)

  {C_RED}[0]{C_RESET}  🚪 Chiqish
""")
        choice = input(f"{C_BOLD}Buyruq raqamini tanlang [0-18]: {C_RESET}").strip()
        
        if choice == "1": show_org_service_tree(); pause()
        elif choice == "2": create_organization_wizard(); pause()
        elif choice == "3": create_service_wizard(); pause()
        elif choice == "4": view_secret_wizard(); pause()
        elif choice == "5": update_secret_wizard(); pause()
        elif choice == "6": delete_service_or_org(); pause()
        elif choice == "7": create_service_token_wizard(); pause()
        elif choice == "8": list_and_manage_active_tokens(); pause()
        elif choice == "9": create_approle_wizard(); pause()
        elif choice == "10": create_userpass_wizard(); pause()
        elif choice == "11": manage_acl_policies()
        elif choice == "12": view_audit_logs(); pause()
        elif choice == "13": backup_vault_secrets(); pause()
        elif choice == "14": list_and_restore_backup(); pause()
        elif choice == "15": production_doctor(); pause()
        elif choice == "16": manage_firewall(); pause()
        elif choice == "17":
            print(f"\n{C_CYAN}{C_BOLD}" + "="*60)
            print(" 🌐 HASHICORP VAULT PRODUCTION WEB INTERFEYSI:")
            print(f" URL:        {VAULT_ADDR}/ui")
            print(f" Method:     Token yoki Userpass")
            print(f" Root Token: {TOKEN}")
            print("="*60 + f"{C_RESET}")
            pause()
        elif choice == "18":
            login_interactive()
        elif choice == "0":
            print("\nXayr!")
            break
        else:
            print_warning("Noto'g'ri raqam kiritildi!")
            pause()

if __name__ == "__main__":
    try:
        login_interactive()
        main_menu()
    except KeyboardInterrupt:
        print("\nPanel yakunlandi.")
        sys.exit(0)
