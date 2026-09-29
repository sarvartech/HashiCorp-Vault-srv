import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Ensure policies exist using root token
root_token = os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")
policy_content = """
path "secret/data/humo/1-token" {
  capabilities = ["read", "list"]
}
path "secret/metadata/humo/1-token" {
  capabilities = ["read", "list"]
}
path "secret/data/humo/*" {
  capabilities = ["read", "list"]
}
"""

url = "https://192.168.86.128/v1/sys/policies/acl/policy-humo-1-token-ro"
headers = {"Host": "vault-srv.trustbank.uz", "X-Vault-Token": root_token}
r = requests.put(url, headers=headers, json={"policy": policy_content}, verify=False)
print("Policy create status:", r.status_code)

# 2. Test reading secret with the user's client token
user_token = os.environ.get("TEST_USER_TOKEN", "YOUR_TEST_USER_TOKEN")
sec_url = "https://192.168.86.128/v1/secret/data/humo/1-token"
sec_headers = {
    "Host": "vault-srv.trustbank.uz",
    "X-Vault-Token": user_token
}
r2 = requests.get(sec_url, headers=sec_headers, verify=False)
print("Secret read status with user token:", r2.status_code)
if r2.status_code == 200:
    print("Secret content:", json.dumps(r2.json()["data"]["data"], indent=2))
else:
    print("Error:", r2.text)
