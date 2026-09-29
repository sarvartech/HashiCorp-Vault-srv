import requests

VAULT_ADDR = "http://192.168.86.128:8200"
import os
ROOT_TOKEN = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")

headers = {
    "X-Vault-Token": ROOT_TOKEN,
    "Content-Type": "application/json"
}

# Lookup token
res = requests.post(f"{VAULT_ADDR}/v1/auth/token/lookup", headers=headers, json={
    "token": os.environ.get("LOOKUP_TOKEN", "YOUR_LOOKUP_TOKEN")
})
print("Token lookup:", res.status_code, res.json())
