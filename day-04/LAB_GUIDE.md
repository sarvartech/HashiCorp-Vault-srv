# 🛠️ DAY 4: AMALIY QO'LLANMA (LAB GUIDE)
## AppRole & HCL Policies Bilan Ishlash

Ushbu amaliyotda biz xavfsiz HCL siyosati yozamiz, AppRole mexanizmini ishga tushiramiz, Role ID va Secret ID olib, dastur nomidan cheklangan huquqli token bilan tizimga kiramiz.

---

### 1-Qadam: Cheklangan Ruxsat Siyosatini (Policy) Yozish

Biz faqat `secret/data/production/database` manzilini o'qishga, `secret/data/staging/*` manziliga esa to'liq ruxsat beruvchi siyosat yaratamiz:

```bash
cat << 'EOF' > backend-app-policy.hcl
# Faqat production database parolini o'qiy olsin
path "secret/data/production/database" {
  capabilities = ["read"]
}

# Staging muhitiga to'liq huquq
path "secret/data/staging/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Boshqa hamma joy avtomatik bloklanadi
EOF
```

Siyosatni Vault'ga yuklash:
```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="<ROOT_TOKEN>"

# Siyosatni yaratish
vault policy write backend-app-policy backend-app-policy.hcl

# Tekshirish
vault policy list
vault policy read backend-app-policy
```

---

### 2-Qadam: AppRole Autentifikatsiyasini Yoqish

```bash
# AppRole auth metodini faollashtirish
vault auth enable approle

# backend-service nomi bilan yangi rol ochish va unga backend-app-policy siyosatini biriktirish
vault write auth/approle/role/backend-service \
    secret_id_ttl=24h \
    token_ttl=1h \
    token_max_ttl=4h \
    policies="backend-app-policy"
```

---

### 3-Qadam: Role ID va Secret ID Olish

Dastur (yoki CI/CD) o'zini tanitishi uchun shu 2 ta kalit kerak:

```bash
# 1. Role ID ni olish (Ochiq ID)
ROLE_ID=$(vault read -field=role_id auth/approle/role/backend-service/role-id)
echo "Role ID: $ROLE_ID"

# 2. Secret ID generatsiya qilish (Maxfiy)
SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/backend-service/secret-id)
echo "Secret ID: $SECRET_ID"
```

---

### 4-Qadam: Dastur Sifatida Login Qilish va Token Olish

Endi tasavvur qiling: biz serverdagi Python yoki Node.js dasturmiz. Bizda Root token yo'q, faqat Role ID va Secret ID bor:

```bash
# REST API orqali login qilib vaqtinchalik client token olish:
APP_TOKEN=$(curl -s --request POST \
    --data "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
    http://127.0.0.1:8200/v1/auth/approle/login | jq -r .auth.client_token)

echo "Dasturning yangi tokeni: $APP_TOKEN"
```

---

### 5-Qadam: Ruxsatlarni Sinash (Allow va Deny Testi)

Keling, dastur tokeni bilan sirlarni o'qib ko'ramiz:

#### Test 1: Ruxsat berilgan sir (`secret/production/database`):
```bash
VAULT_TOKEN=$APP_TOKEN vault kv get secret/production/database
```
✅ **Natija:** Muvaffaqiyatli o'qildi!

#### Test 2: Ruxsat berilmagan sir (`secret/payments/stripe`):
```bash
VAULT_TOKEN=$APP_TOKEN vault kv get secret/payments/stripe
```
❌ **Natija:** `Error: permission denied` (403 Forbidden). Siyosat o'z vazifasini 100% bajardi!

---

### 🎯 Day 4 Mini-Topshiriq:
1. `userpass` autentifikatsiyasini yoqing: `vault auth enable userpass`.
2. `junior_dev` foydalanuvchisini yarating: `vault write auth/userpass/users/junior_dev password="Pass123!" policies="backend-app-policy"`.
3. CLI orqali o'sha foydalanuvchi nomidan kiring: `vault login -method=userpass username=junior_dev`.
