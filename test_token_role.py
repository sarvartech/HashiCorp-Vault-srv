import requests
import json

import os
VAULT_ADDR = "http://192.168.86.128:8200"
ROOT_TOKEN = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")

headers = {
    "X-Vault-Token": ROOT_TOKEN,
    "Content-Type": "application/json"
}

# 1. Create a token-role with bound_cidrs
r_role = requests.post(f"{VAULT_ADDR}/v1/auth/token/roles/ip-restricted-role", headers=headers, json={
    "allowed_policies": ["policy-fintech-group-billing-service-ro"],
    "bound_cidrs": ["192.168.86.99/32"], # only 192.168.86.99 allowed
    "token_ttl": "1h"
})
print("Create token role:", r_role.status_code)

# 2. Issue a token from this role
r_tok = requests.post(f"{VAULT_ADDR}/v1/auth/token/create/ip-restricted-role", headers=headers, json={})
print("Issue token from role:", r_tok.status_code, r_tok.text)

# 3. If issued, test reading secret from 192.168.86.1 (should fail with permission denied!)
if r_tok.status_code == 200:
    t = r_tok.json().get("auth", {}).get("client_token")
    r_test = requests.get(f"{VAULT_ADDR}/v1/secret/data/fintech-group/billing-service", headers={"X-Vault-Token": t})
    print("Read with IP-restricted token from unauthorized IP:", r_test.status_code, r_test.text)
