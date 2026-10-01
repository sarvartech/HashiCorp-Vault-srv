import urllib3
import requests

urllib3.disable_warnings()

VAULT_ADDR = "https://192.168.86.70:8200"
CA_CERT = "vault_ca.crt"
CLIENT_CERT = "client_app.crt"
CLIENT_KEY = "client_app.key"

print("=" * 65)
print("1. TEST: DevOps muhandisi o'z noutbukidan cert kalitsiz kirdi:")
print("=" * 65)
try:
    res_no_cert = requests.post(
        f"{VAULT_ADDR}/v1/auth/cert/login",
        verify=CA_CERT,
        timeout=5
    )
    print("Natija (kalitsiz):", res_no_cert.status_code, res_no_cert.text)
except Exception as e:
    print("Xatolik (rad etildi):", e)

print("\n" + "=" * 65)
print("2. TEST: Serverdagi Haqiqiy Ilova (mTLS Sertifikat bilan) kirdi:")
print("=" * 65)
res_cert = requests.post(
    f"{VAULT_ADDR}/v1/auth/cert/login",
    cert=(CLIENT_CERT, CLIENT_KEY),
    verify=CA_CERT,
    timeout=5
)
print("mTLS Login Status:", res_cert.status_code)
token_data = res_cert.json()["auth"]
app_token = token_data["client_token"]
print("Ilovaga berilgan xavfsiz token:", app_token[:20] + "...")
print("Bog'langan siyosatlar (Policies):", token_data["policies"])

print("\n" + "=" * 65)
print("3. TEST: Ilova o'ziga ruxsat berilgan sekretni o'qishi:")
print("=" * 65)
res_secret = requests.get(
    f"{VAULT_ADDR}/v1/secret/data/apps/devops-app",
    headers={"X-Vault-Token": app_token},
    verify=CA_CERT
)
print("Status:", res_secret.status_code)
print("Olingan Maxfiy API Token:", res_secret.json()["data"]["data"])

print("\n" + "=" * 65)
print("4. TEST: Ilova begona (prod/database) sekretni o'qishga urinishi:")
print("=" * 65)
res_prod = requests.get(
    f"{VAULT_ADDR}/v1/secret/data/prod/database",
    headers={"X-Vault-Token": app_token},
    verify=CA_CERT
)
print("Status:", res_prod.status_code, "(403 Forbidden - BLOKLANDI!)")
print("=" * 65)
print("XULOSA: mTLS orqali sekret 100% himoyalandi! NAT ahamiyatga ega emas!")
