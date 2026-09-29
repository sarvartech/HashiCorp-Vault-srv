import requests
import urllib3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROLE_ID = "8df244fc-57e8-9eac-10d2-bad18961fa35"
SECRET_ID = "2c9da07d-0103-dbb1-ad04-a7c3bba783cd"

# 1. Login with AppRole via HTTPS (IP + Host header)
url = "https://192.168.86.128/v1/auth/approle/login"
headers = {"Host": "vault-srv.trustbank.uz", "Content-Type": "application/json"}
payload = {"role_id": ROLE_ID, "secret_id": SECRET_ID}

print("1. AppRole orqali login qilinmoqda...")
r = requests.post(url, headers=headers, json=payload, verify=False, timeout=5)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    client_token = r.json()["auth"]["client_token"]
    print(f"✔ Client Token olindi: {client_token}")
    
    # 2. Read Secret: secret/data/humo/1-token
    print("\n2. Secret o'qilmoqda: secret/data/humo/1-token...")
    sec_url = "https://192.168.86.128/v1/secret/data/humo/1-token"
    sec_headers = {
        "Host": "vault-srv.trustbank.uz",
        "X-Vault-Token": client_token
    }
    r2 = requests.get(sec_url, headers=sec_headers, verify=False, timeout=5)
    print(f"Status: {r2.status_code}")
    print("Secret ma'lumotlari:")
    print(json.dumps(r2.json().get("data", {}).get("data", {}), indent=2))
else:
    print(f"Xatolik: {r.text}")
