import requests

VAULT_ADDR = "http://192.168.86.128:8200"
import os
ROOT_TOKEN = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")

headers = {
    "X-Vault-Token": ROOT_TOKEN,
    "Content-Type": "application/json"
}

# Bind IP to billing-service secret
res = requests.get(f"{VAULT_ADDR}/v1/secret/data/fintech-group/billing-service", headers=headers)
data = res.json()["data"]["data"]
data["_bound_source_ip"] = "192.168.86.50"

requests.post(f"{VAULT_ADDR}/v1/secret/data/fintech-group/billing-service", headers=headers, json={"data": data})
print("Bound IP 192.168.86.50 to billing-service secret successfully!")
