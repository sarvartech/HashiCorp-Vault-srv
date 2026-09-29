import requests

import os
VAULT_ADDR = "http://192.168.86.128:8200"
ROOT_TOKEN = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")

headers = {
    "X-Vault-Token": ROOT_TOKEN,
    "Content-Type": "application/json"
}

# 1. Create a token-role with our actual IP 192.168.86.1/32
r_role = requests.post(f"{VAULT_ADDR}/v1/auth/token/roles/ip-allowed-role", headers=headers, json={
    "allowed_policies": ["policy-fintech-group-billing-service-ro"],
    "bound_cidrs": ["192.168.86.1/32"],
    "token_ttl": "1h"
})

r_tok = requests.post(f"{VAULT_ADDR}/v1/auth/token/create/ip-allowed-role", headers=headers, json={})
t = r_tok.json().get("auth", {}).get("client_token")

r_test = requests.get(f"{VAULT_ADDR}/v1/secret/data/fintech-group/billing-service", headers={"X-Vault-Token": t})
print("Read with IP-restricted token from AUTHORIZED IP:", r_test.status_code, "Keys:", list(r_test.json().get("data", {}).get("data", {}).keys()))
