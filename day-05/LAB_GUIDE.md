# 🛠️ DAY 5: AMALIY QO'LLANMA (LAB GUIDE)
## PKI Engine Bilan Shaxsiy CA va SSL Sertifikatlar Generatsiyasi

Ushbu amaliyotda biz Vault ichida o'zimizning Root Certificate Authority (CA) tuzilmamizni quramiz, ichki domenlar uchun rol yaratamiz va avtomatlashtirilgan SSL sertifikat olamiz.

---

### 1-Qadam: PKI Secret Engine'ni Yoqish

```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="<ROOT_TOKEN>"

# PKI engine'ni yoqish
vault secrets enable pki

# Sertifikatning maksimal muddatini 10 yilga belgilash (87600 soat)
vault secrets tune -max-lease-ttl=87600h pki
```

---

### 2-Qadam: Xususiy Root CA Yaratish

Vault'ning o'zida ichki o'zini imzolaydigan Root CA generatsiya qilamiz:

```bash
vault write -field=certificate pki/root/generate/internal \
    common_name="DevOps Company Internal Root CA" \
    ttl=87600h > root_ca.crt

echo "Root CA sertifikati saqlandi: root_ca.crt"
```

Vault uchun CRL (Certificate Revocation List) va CA manzillarini sozlash:
```bash
vault write pki/config/urls \
    issuing_certificates="http://192.168.0.250:8200/v1/pki/ca" \
    crl_distribution_points="http://192.168.0.250:8200/v1/pki/crl"
```

---

### 3-Qadam: Sertifikat Beruvchi Rolni (Role) Sozlash

Endi dasturchilar yoki serverlar qanday domenlarga sertifikat so'rashi mumkinligini qoidaga solamiz:

```bash
vault write pki/roles/internal-services \
    allowed_domains="internal.local,devops.lan" \
    allow_subdomains=true \
    max_ttl="720h" # Maksimal 30 kunlik muddat
```

---

### 4-Qadam: Talabga Binoan (On-Demand) SSL Sertifikat Olish

Keling, ichki mikroservisimiz (`api.internal.local`) uchun SSL sertifikat chiqaramiz:

```bash
vault write -format=json pki/issue/internal-services \
    common_name="api.internal.local" \
    ttl="720h" > cert_response.json

# JSON ichidan sertifikat va maxfiy kalitni ajratib olish:
jq -r .data.certificate cert_response.json > api_service.crt
jq -r .data.private_key cert_response.json > api_service.key
jq -r .data.issuing_ca cert_response.json > ca_chain.crt
```

Sertifikat haqiqiy ekanini OpenSSL orqali tekshiramiz:
```bash
openssl x509 -in api_service.crt -text -noout | grep -E "Issuer|Subject|Not After"
```
> Ko'rib turganingizdek, sertifikat 1 soniya ichida tayyor bo'ldi va uning egasi (Issuer) bizning Vault Root CA!

---

### 5-Qadam: Sertifikatni Bekor Qilish (Revocation)

Agar server xakerlar qo'liga tushsa, sertifikatning seriya raqami bo'yicha uni bir zumda bekor qilamiz:

```bash
SERIAL_NUMBER=$(jq -r .data.serial_number cert_response.json)
echo "Bekor qilinayotgan seriya raqam: $SERIAL_NUMBER"

# Sertifikatni bekor qilish
vault write pki/revoke serial_number=$SERIAL_NUMBER
```

---

### 🎯 Day 5 Mini-Topshiriq:
1. `nginx.internal.local` domeni uchun yangi sertifikat generatsiya qiling.
2. Serveringizda Nginx o'rnatib (`apt install nginx`), unga ushbu `.crt` va `.key` fayllarni ulab, HTTPS orqali ishlab turganini tekshiring.
