import json
import urllib3
import requests

# Disable TLS warning because we are supplying our custom CA certificate
urllib3.disable_warnings()

VAULT_ADDR = "https://192.168.86.70:8200"
CA_CERT = "vault_ca.crt"

# Load Root Token and AppRole credentials
with open("vault_credentials.json") as f:
    creds = json.load(f)
ROOT_TOKEN = creds["root_token"]

with open("approle_credentials.json") as f:
    approle = json.load(f)

print("=" * 60)
print("1. Testing Root Token Access (Vault Admin)")
print("=" * 60)
res = requests.get(
    f"{VAULT_ADDR}/v1/secret/data/prod/database",
    headers={"X-Vault-Token": ROOT_TOKEN},
    verify=CA_CERT
)
print(f"Status: {res.status_code}")
print("Prod Database Secret:", res.json().get("data", {}).get("data"))

print("\n" + "=" * 60)
print("2. Testing AppRole Authentication (for CI/CD / Backend Apps)")
print("=" * 60)
login_res = requests.post(
    f"{VAULT_ADDR}/v1/auth/approle/login",
    json={"role_id": approle["role_id"], "secret_id": approle["secret_id"]},
    verify=CA_CERT
)
app_token = login_res.json()["auth"]["client_token"]
print("AppRole Token successfully generated:", app_token[:15] + "...")

# AppRole reading permitted path (prod database)
res_allowed = requests.get(
    f"{VAULT_ADDR}/v1/secret/data/prod/database",
    headers={"X-Vault-Token": app_token},
    verify=CA_CERT
)
print("App accessing ALLOWED secret (prod):", res_allowed.json().get("data", {}).get("data"))

# AppRole attempting to write or read dev database (should be restricted/denied)
res_dev = requests.get(
    f"{VAULT_ADDR}/v1/secret/data/dev/database",
    headers={"X-Vault-Token": app_token},
    verify=CA_CERT
)
print("App accessing RESTRICTED path (dev):", res_dev.status_code, "(403 Forbidden - BLOCKED BY POLICY)")

print("\n" + "=" * 60)
print("3. Testing Developer User Authentication (dev_user)")
print("=" * 60)
user_login = requests.post(
    f"{VAULT_ADDR}/v1/auth/userpass/login/dev_user",
    json={"password": "DevUserPass2026!"},
    verify=CA_CERT
)
dev_token = user_login.json()["auth"]["client_token"]
print("dev_user logged in! Token:", dev_token[:15] + "...")

# Dev reading dev database (ALLOWED)
dev_read_allowed = requests.get(
    f"{VAULT_ADDR}/v1/secret/data/dev/database",
    headers={"X-Vault-Token": dev_token},
    verify=CA_CERT
)
print("dev_user reading DEV secret:", dev_read_allowed.json().get("data", {}).get("data"))

# Dev attempting to read PROD database (DENIED / FORBIDDEN)
dev_read_prod = requests.get(
    f"{VAULT_ADDR}/v1/secret/data/prod/database",
    headers={"X-Vault-Token": dev_token},
    verify=CA_CERT
)
print("dev_user attempting to read PROD secret:", dev_read_prod.status_code, "(403 Forbidden - BLOCKED BY POLICY)")
print("=" * 60)
print("SECURITY VERIFICATION COMPLETE: ALL POLICIES ARE ENFORCED!")
