import requests
import json

VAULT_ADDR = "http://192.168.86.128:8200"
import os
ROOT_TOKEN = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")

headers = {
    "X-Vault-Token": ROOT_TOKEN,
    "Content-Type": "application/json"
}

# 1. Create token bound to IP 192.168.86.1/32 (our host Windows IP)
res = requests.post(f"{VAULT_ADDR}/v1/auth/token/create", headers=headers, json={
    "policies": ["policy-fintech-group-billing-service-ro"],
    "bound_cidrs": ["192.168.86.1/32"],
    "ttl": "1h"
})
print("Create token bound to 192.168.86.1:", res.status_code, res.json().get("auth", {}).get("client_token"))

# 2. Try to read secret with this token from 192.168.86.1 (should succeed!)
tok1 = res.json().get("auth", {}).get("client_token")
r_read = requests.get(f"{VAULT_ADDR}/v1/secret/data/fintech-group/billing-service", headers={"X-Vault-Token": tok1})
print("Read with allowed IP token:", r_read.status_code, "Keys:", list(r_read.json().get("data", {}).get("data", {}).keys()) if r_read.status_code == 200 else r_read.text)

# 3. Create token bound to a fake IP 192.168.86.99/32
res2 = requests.post(f"{VAULT_ADDR}/v1/auth/token/create", headers=headers, json={
    "policies": ["policy-fintech-group-billing-service-ro"],
    "bound_cidrs": ["192.168.86.99/32"],
    "ttl": "1h"
})
tok2 = res2.json().get("auth", {}).get("client_token")
print("Create token bound to 192.168.86.99:", res2.status_code, tok2)

# 4. Try to read secret with tok2 from 192.168.86.1 (should FAIL with 403 / permission denied!)
r_read2 = requests.get(f"{VAULT_ADDR}/v1/secret/data/fintech-group/billing-service", headers={"X-Vault-Token": tok2})
print("Read with blocked IP token:", r_read2.status_code, r_read2.text)
