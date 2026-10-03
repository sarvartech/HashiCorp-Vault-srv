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

### 6-Qadam: Superadmin Policy va Yangi Admin User Yaratish

Root tokenni xavfsiz bekor qilishdan oldin, barcha ma'muriy huquqlarga ega shaxsiy Admin foydalanuvchisi ochilishi shart.

```bash
# 1. Admin siyosati faylini yaratamiz
cat << 'EOF' > admin-policy.hcl
# Vault'dagi barcha yo'llarga to'liq kirish va boshqaruv (sudo) huquqi
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EOF

# 2. Siyosatni Vault'ga yuklaymiz
vault policy write admin admin-policy.hcl

# 3. Userpass autentifikatsiyasini yoqamiz (agar oldin yoqilmagan bo'lsa)
vault auth enable userpass

# 4. Yangi shaxsiy Admin foydalanuvchi yaratamiz
vault write auth/userpass/users/sarvar_admin \
    password="AdminStrongPassword2026!" \
    policies="admin"
```

---

### 7-Qadam: Yangi Admin Bilan Login Qilish va Huquqlarni Sinash

Hech qachon yangi admin hisobini tekshirib ko'rmasdan eski tokenlarni o'chirmang:

```bash
# Yangi admin bilan login qilamiz
vault login -method=userpass username=sarvar_admin
# Parolni kiriting: AdminStrongPassword2026!

# Token ma'lumotlarini tekshiramiz
vault token lookup
```
✅ Siz `policies: [admin default]` ga ega yangi faol tokenga ega bo'lasiz.

---

### 8-Qadam: Foydalanuvchilarni Boshqarish va O'chirish (Remove User)

Keling, oddiy dasturchi hisobini ochib, so'ng uni tizimdan o'chirishni (Offboarding) bajaramiz:

```bash
# 1. Sinov uchun yangi user yaratamiz
vault write auth/userpass/users/test_dev \
    password="TempPassword123!" \
    policies="backend-app-policy"

# 2. Mavjud barcha foydalanuvchilar ro'yxatini ko'ramiz
vault list auth/userpass/users

# 3. Foydalanuvchi ma'lumotlarini o'qish (qaysi siyosatlar biriktirilgan)
vault read auth/userpass/users/test_dev

# 4. Foydalanuvchining parolini yoki siyosatini yangilash (Update)
vault write auth/userpass/users/test_dev \
    password="NewSuperPassword2026!" \
    policies="backend-app-policy,default"

# 5. Foydalanuvchini tizimdan butunlay O'CHIRISH (Remove / Delete)
vault delete auth/userpass/users/test_dev

# 6. O'chirilganini tekshirish
vault list auth/userpass/users
```
> [!IMPORTANT]
> `vault delete auth/userpass/users/<username>` buyrug'i foydalanuvchining yangi login qilishini darhol to'xtatadi. Agar uning oldin olingan faol tokeni qolgan bo'lsa, uni `vault token revoke -accessor <ACCESSOR_ID>` orqali bekor qilasiz.

---

### 🎯 Day 4 Topshiriq:
1. O'zingiz uchun shaxsiy `ism_admin` nomli foydalanuvchi yarating va unga `admin` siyosatini bering.
2. Yangi yaratilgan admingiz bilan login qilib, tizim holatini (`vault status`) tekshiring.
3. Soxta `fired_employee` foydalanuvchisini yarating va uni `vault delete` buyrug'i bilan o'chirib tashlang.

