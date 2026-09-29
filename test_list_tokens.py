import requests
import json

VAULT_ADDR = "http://192.168.86.128:8200"
import os
ROOT_TOKEN = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")

headers = {
    "X-Vault-Token": ROOT_TOKEN,
    "Content-Type": "application/json"
}

# List accessors
res = requests.get(f"{VAULT_ADDR}/v1/auth/token/accessors?list=true", headers=headers)
print("Accessors status:", res.status_code)
accessors = res.json().get("data", {}).get("keys", [])
print(f"Total tokens found: {len(accessors)}")

for acc in accessors[:5]:
    info = requests.post(f"{VAULT_ADDR}/v1/auth/token/lookup-accessor", headers=headers, json={"accessor": acc})
    if info.status_code == 200:
        d = info.json()["data"]
        print(f"Accessor: {acc} | Display: {d.get('display_name')} | Policies: {d.get('policies')} | TTL: {d.get('ttl')}")
