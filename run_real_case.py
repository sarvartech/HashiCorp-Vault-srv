import requests
import json

VAULT_ADDR = "http://192.168.86.128:8200"
import os
ROOT_TOKEN = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")

headers = {
    "X-Vault-Token": ROOT_TOKEN,
    "Content-Type": "application/json"
}

# 1. Real Case Tashkilot va Servis
org = "kapitalbank"
service = "payment-gateway"
source_ip = "192.168.86.1" # Bizning haqiqiy IP

# Setup policies
policy_rw = f"""
path "secret/data/{org}/{service}" {{ capabilities = ["create", "read", "update", "delete", "list"] }}
path "secret/metadata/{org}/{service}" {{ capabilities = ["read", "list"] }}
"""
policy_ro = f"""
path "secret/data/{org}/{service}" {{ capabilities = ["read"] }}
path "secret/metadata/{org}/{service}" {{ capabilities = ["read", "list"] }}
"""
requests.put(f"{VAULT_ADDR}/v1/sys/policies/acl/policy-{org}-{service}-rw", headers=headers, json={"policy": policy_rw})
requests.put(f"{VAULT_ADDR}/v1/sys/policies/acl/policy-{org}-{service}-ro", headers=headers, json={"policy": policy_ro})

# 2. Secret yozish
sec_payload = {
    "data": {
        "service": service,
        "organization": org,
        "db_host": "pg-cluster.kapitalbank.uz",
        "db_user": "pg_payment_app",
        "db_password": "K@p1tal_SecPass_2026!#",
        "merchant_id": "KB_MERCH_778129",
        "api_secret_key": "vlt_sec_live_9f81a7b420e6c138",
        "_bound_source_ip": source_ip
    }
}
r_put = requests.post(f"{VAULT_ADDR}/v1/secret/data/{org}/{service}", headers=headers, json=sec_payload)

# 3. IP-Locked Token yaratish
token_role_name = f"trole-{org}-{service}-app"
requests.post(f"{VAULT_ADDR}/v1/auth/token/roles/{token_role_name}", headers=headers, json={
    "allowed_policies": [f"policy-{org}-{service}-ro"],
    "bound_cidrs": [f"{source_ip}/32"],
    "token_ttl": "24h"
})

r_tok = requests.post(f"{VAULT_ADDR}/v1/auth/token/create/{token_role_name}", headers=headers, json={
    "display_name": f"{org}-{service}-backend"
})
tok_data = r_tok.json().get("auth", {})
client_token = tok_data.get("client_token")
accessor = tok_data.get("accessor")

print("REAL CASE YARATILDI:")
print("Client Token:", client_token)
print("Accessor:", accessor)

# 4. Haqiqiy dasturchi so'rovi (Ruxsatli IP 192.168.86.1 dan o'qish):
dev_res = requests.get(f"{VAULT_ADDR}/v1/secret/data/{org}/{service}", headers={"X-Vault-Token": client_token})
print("Dasturchi so'rovi javobi (Status):", dev_res.status_code)
print("Secretlar:", json.dumps(dev_res.json()["data"]["data"], indent=2))
