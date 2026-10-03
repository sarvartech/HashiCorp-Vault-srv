# ⚡ HASHICORP VAULT CRUD & OPERATOR CHEAT SHEET
> **Tizim:** `https://vault-srv.sarvartech.uz` | **Tashkilot:** `sarvartech`  
> *Administratorlar, DevOps muhandislari va dasturchilar uchun barcha CRUD (Create, Read, Update, Delete) amallari, buyruqlar va REST API to'plami.*

---

## 📑 CHEAT SHEET MUNDARIJASI
1. [Secrets (KV v2) CRUD & Versiyalash](#1-secrets-kv-v2-crud--versiyalash)
2. [Vault Buyruqlar Sintaksisining To'liq Anatomiyasi (PUT, GET, INPUT, LIST, OVERVIEW)](#2-vault-buyruqlar-sintaksisining-toliq-anatomiyasi-put-get-input-list-overview)
3. [ACL Policies (Xavfsizlik Siyosati) CRUD](#3-acl-policies-crud)
4. [AppRole & Secret-ID (Mikroservislar) CRUD](#4-approle--secret-id-crud)
5. [Foydalanuvchilar (Userpass & Admin) CRUD Boshqaruvi](#5-foydalanuvchilar-userpass--admin-crud-boshqaruvi)
6. [Unseal, Seal, Tokenlar & Accessor Boshqaruvi](#6-unseal-seal-tokenlar--accessor-boshqaruvi)
7. [Ekspress Qidiruv: Eng Ko'p Ishlatiladigan 10 Ta Buyruq](#7-eng-kop-ishlatiladigan-10-ta-buyruq)

---

## 1. SECRETS (KV v2) CRUD & VERSIYALASH

> **Yo'l strukturasi:** `secret/data/organizations/sarvartech/{service}/{env}`

| Amal | CLI Buyrug'i | REST API (cURL) | Izoh / Natija |
| :--- | :--- | :--- | :--- |
| **CREATE (Yozish)** | `vault kv put secret/organizations/sarvartech/billing/prod db_user="admin" db_pass="P@ss2026"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"data": {"db_user": "admin", "db_pass": "P@ss2026"}}' https://vault-srv.sarvartech.uz/v1/secret/data/organizations/sarvartech/billing/prod` | Yangi secret yaratadi yoki yangi versiya (v1, v2...) ochadi. |
| **READ (O'qish - Eng so'nggi)** | `vault kv get secret/organizations/sarvartech/billing/prod` | `curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/secret/data/organizations/sarvartech/billing/prod \| jq .data.data` | Eng oxirgi faol versiyaning qiymatlarini o'qiydi. |
| **READ (Aniq versiyani o'qish)** | `vault kv get -version=1 secret/organizations/sarvartech/billing/prod` | `curl -H "X-Vault-Token: $TOKEN" "https://vault-srv.sarvartech.uz/v1/secret/data/organizations/sarvartech/billing/prod?version=1" \| jq .data.data` | Tarixdagi 1-versiya parollarini chiqaradi. |
| **UPDATE (Patch - Qisman yangilash)** | `vault kv patch secret/organizations/sarvartech/billing/prod api_key="sk_live_9921"` | `curl -X PATCH -H "X-Vault-Token: $TOKEN" -H "Content-Type: application/merge-patch+json" -d '{"data": {"api_key": "sk_live_9921"}}' https://vault-srv.sarvartech.uz/v1/secret/data/organizations/sarvartech/billing/prod` | **Eski kalitlarni o'chirmasdan**, faqat yangi kalitni qo'shadi yoki yangilaydi. |
| **LIST (Papkalar ro'yxati)** | `vault kv list secret/organizations/sarvartech/` | `curl -X LIST -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/secret/metadata/organizations/sarvartech/` | Ichidagi barcha servislar va kataloglarni ko'rsatadi. |
| **DELETE (Soft Delete - Versiyani yashirish)** | `vault kv delete -versions=2 secret/organizations/sarvartech/billing/prod` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"versions": [2]}' https://vault-srv.sarvartech.uz/v1/secret/delete/organizations/sarvartech/billing/prod` | 2-versiyani o'chiradi (kerak bo'lsa tiklab olinadi). |
| **UNDELETE (Versiyani qayta tiklash)** | `vault kv undelete -versions=2 secret/organizations/sarvartech/billing/prod` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"versions": [2]}' https://vault-srv.sarvartech.uz/v1/secret/undelete/organizations/sarvartech/billing/prod` | Adashib o'chirilgan versiyani darhol qayta tiriltiradi. |
| **DESTROY (Butunlay yo'q qilish)** | `vault kv destroy -versions=2 secret/organizations/sarvartech/billing/prod` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"versions": [2]}' https://vault-srv.sarvartech.uz/v1/secret/destroy/organizations/sarvartech/billing/prod` | 2-versiyani **butunlay yo'q qiladi** (Tiklab bo'lmaydi!). |
| **METADATA DELETE (To'liq tozalash)** | `vault kv metadata delete secret/organizations/sarvartech/billing/prod` | `curl -X DELETE -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/secret/metadata/organizations/sarvartech/billing/prod` | Barcha versiyalari va tarixi bilan birga ildizidan o'chiradi. |

---

## 2. VAULT BUYRUQLAR SINTAKSISINING TO'LIQ ANATOMIYASI (PUT, GET, INPUT, LIST, OVERVIEW)

Vault CLI barcha Unix/Linux dasturchilar uchun juda intuitiv va kuchli sintaksisga ega. Har bir buyruqning ishlash mexanizmi quyidagicha:

### 📌 1. `OVERVIEW` — Buyruqlar Falsafasi va Darajalari
Vaultda buyruqlar 2 ta katta guruhga bo'linadi:

1. **High-Level (KV v2 Maxsus Buyruqlari):**
   * Sintaksis: `vault kv <subcommand> [yo'l] [parametrlar]`
   * Masalan: `vault kv put`, `vault kv get`, `vault kv patch`, `vault kv list`, `vault kv undelete`.
   * *Afzalligi:* Avtomatik ravishda `/data/` va `/metadata/` prefikslarini o'zi qo'yadi, versiyalashni o'zi boshqaradi.
2. **Low-Level (Generic REST API Buyruqlari):**
   * Sintaksis: `vault <read|write|list|delete> [to'liq_api_yo'l]`
   * Masalan: `vault read secret/data/organizations/sarvartech/billing/prod`
   * *Qachon kerak:* `sys/`, `auth/`, `pki/`, `transit/` kabi tizim dvigatellari bilan ishlashda.
3. 💡 **Oltin Flag: `-output-curl-string`**
   * Agar har qanday Vault buyrug'iga ushbu flagni qo'shsangiz, u buyruqni bajarmasdan unga **100% teng keladigan tayyor `curl` so'rovini** ekranga chiqarib beradi:
   ```bash
   vault kv get -output-curl-string secret/organizations/sarvartech/billing/prod
   # Natija: curl -H "X-Vault-Token: ..." https://vault-srv.sarvartech.uz/v1/secret/data/...
   ```

---

### 📌 2. `PUT` — Ma'lumot Yozish va Saqlash Sintaksisi
`put` buyrug'i berilgan yo'lga yangi secret yozadi yoki yangi versiya (v1 ➔ v2 ➔ v3) ochadi:

```bash
# 1. Inline (Bir nechta kalit-qiymatlarni qatorda yozish):
vault kv put secret/organizations/sarvartech/billing/prod \
    db_host="192.168.10.15" \
    db_port=5432 \
    db_user="billing_admin" \
    db_pass="SuperSecret@2026"

# 2. Fayldan o'qib yozish (@ prefiksi bilan):
# Agar kalit qiymati uzun sertifikat, SSH private key yoki config bo'lsa:
vault kv put secret/organizations/sarvartech/billing/prod \
    tls_cert=@/etc/ssl/certs/app.crt \
    tls_key=@/etc/ssl/private/app.key

# 3. Butun bir JSON faylni bitta zarbda yuklash:
vault kv put secret/organizations/sarvartech/billing/prod @appsettings.json

# 4. Check-and-Set (-cas) optimistik blokirovkasi:
# Faqat joriy versiya 2 bo'lsagina ustiga yozadi. Agar boshqa admin 3 qilib qo'ygan bo'lsa xato qaytaradi:
vault kv put -cas=2 secret/organizations/sarvartech/billing/prod db_pass="NewPass2026"
```

---

### 📌 3. `GET` — Ma'lumotni O'qish va Filtrlash Sintaksisi
`get` buyrug'i maxfiy ma'lumotlarni o'qib, turli formatlarda taqdim etadi:

```bash
# 1. Standart o'qish (Eng oxirgi faol versiyani chiroyli jadvalda chiqaradi):
vault kv get secret/organizations/sarvartech/billing/prod

# 2. Tarixdagi aniq bir versiyani o'qish (-version):
vault kv get -version=1 secret/organizations/sarvartech/billing/prod

# 3. Dasturchilar uchun eng kerakli flag: -field (Faqat bitta maydon qiymatini olish)
# Bash scriptlarda o'zgaruvchiga parolni yuklash:
DB_PASSWORD=$(vault kv get -field=db_pass secret/organizations/sarvartech/billing/prod)
echo "Yuklangan parol: $DB_PASSWORD"

# 4. JSON formatda chiqarish va jq bilan filtrlash (-format=json):
vault kv get -format=json secret/organizations/sarvartech/billing/prod | jq -r '.data.data.api_token'

# 5. YAML formatda chiqarish (-format=yaml - Kubernetes / Ansible uchun):
vault kv get -format=yaml secret/organizations/sarvartech/billing/prod
```

---

### 📌 4. `INPUT` — Vaultga Ma'lumot Kiritishning 5 Ta Usuli
Dasturchi va administratorlar ma'lumotni turli manbalardan uzatishi mumkin:

1. **Inline Key-Value:**
   `vault kv put secret/path key="qiymat" user="admin"`
2. **Fayl orqali (`@`):**
   `vault kv put secret/path id_rsa=@~/.ssh/id_rsa`
3. **Standart Kirish Oqimi (`stdin` orqali `-` belgisi):**
   ```bash
   cat credentials.json | vault kv put secret/organizations/sarvartech/billing/prod -
   # yoki:
   echo '{"token": "live_sec_123"}' | vault kv put secret/organizations/sarvartech/billing/prod -
   ```
4. **Heredoc Sintaksisi (Fayl yaratmasdan multiline kiritish):**
   ```bash
   vault policy write developer-policy - <<EOF
   path "secret/data/organizations/sarvartech/*" {
     capabilities = ["read", "list"]
   }
   EOF
   ```
5. **Muhit O'zgaruvchilari (Environment Variables):**
   * `VAULT_ADDR` — Server manzili (`https://vault-srv.sarvartech.uz`)
   * `VAULT_TOKEN` — Sessiya tokeni (`hvs.CAES...`)
   * `VAULT_FORMAT` — Standart chiqish formati (`json`, `table`, `yaml`)
   * `VAULT_SKIP_VERIFY` — Test serverlarda SSL tekshiruvini chetlab o'tish (`1` yoki `0`)

---

### 📌 5. `LIST` — Kataloglar va Ob'yektlarni Ko'rish Sintaksisi
`list` katalog ichidagi mavjud kalitlar va papkalarni daraxt ko'rinishida ko'rsatadi:

```bash
# 1. Tashkilot ichidagi barcha servislarni ko'rish:
# MUHIM: Katalog bo'lgani uchun oxirida albatta "/" (slash) bo'lishi shart!
vault kv list secret/organizations/sarvartech/

# 2. Servis ichidagi muhitlarni ko'rish:
vault kv list secret/organizations/sarvartech/billing/
# Natija:
# Keys
# ----
# dev
# prod
# stage

# 3. JSON formatda olish (avtomatlashtirish va scriptlar uchun):
vault kv list -format=json secret/organizations/sarvartech/ | jq -r '.[]'

# 4. Generic Low-Level List (sys va auth uchun):
vault list sys/policies/acl
vault list auth/approle/role/
```

---

## 3. ACL POLICIES CRUD

> Siyosatlar yozish va xavfsizlik huquqlarini tekshirish amallari.

| Amal | CLI Buyrug'i | REST API (cURL) | Izoh / Natija |
| :--- | :--- | :--- | :--- |
| **CREATE / UPDATE (Yozish)** | `vault policy write billing-policy - <<EOF`<br>`path "secret/data/organizations/sarvartech/billing/*" { capabilities = ["read", "list"] }`<br>`EOF` | `curl -X PUT -H "X-Vault-Token: $TOKEN" -d '{"policy": "path \"secret/data/organizations/sarvartech/billing/*\" { capabilities = [\"read\"] }"}' https://vault-srv.sarvartech.uz/v1/sys/policies/acl/billing-policy` | Yangi ACL qoidasini yaratadi yoki ustiga yozadi. |
| **READ (O'qish)** | `vault policy read billing-policy` | `curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/sys/policies/acl/billing-policy \| jq -r .data.policy` | Siyosat qoidalarini terminalda HCL ko'rinishida chiqaradi. |
| **LIST (Barcha siyosatlar)** | `vault policy list` | `curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/sys/policies/acl \| jq .data.policies` | Serverdagi mavjud barcha siyosatlar ro'yxatini beradi. |
| **DELETE (O'chirish)** | `vault policy delete billing-policy` | `curl -X DELETE -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/sys/policies/acl/billing-policy` | Siyosatni o'chirib tashlaydi. |
| **TEST CAPABILITIES (Huquqni sinash)** | `vault token capabilities <TOKEN> secret/data/organizations/sarvartech/billing/prod` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"token": "hvs.CAES...", "paths": ["secret/data/organizations/sarvartech/billing/prod"]}' https://vault-srv.sarvartech.uz/v1/sys/capabilities` | Token ushbu yo'lga nimalar qila olishini (`read, list, deny`) tekshiradi. |

---

## 4. APPROLE & SECRET-ID CRUD

> Mikroservislar va CI/CD tizimlari uchun inson aralashuvisiz kirish.

| Amal | CLI Buyrug'i | REST API (cURL) | Izoh / Natija |
| :--- | :--- | :--- | :--- |
| **CREATE ROLE (Rol yaratish)** | `vault write auth/approle/role/billing-app secret_id_ttl=24h token_ttl=1h token_max_ttl=4h policies="billing-policy"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"secret_id_ttl": "24h", "token_ttl": "1h", "policies": ["billing-policy"]}' https://vault-srv.sarvartech.uz/v1/auth/approle/role/billing-app` | Mikroservis uchun yangi AppRole profili yaratadi. |
| **READ ROLE-ID (Role-ID olish)** | `vault read auth/approle/role/billing-app/role-id` | `curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/approle/role/billing-app/role-id \| jq -r .data.role_id` | Servisning `role_id` (login) qiymatini qaytaradi. |
| **CREATE SECRET-ID (Parol yaratish)** | `vault write -f auth/approle/role/billing-app/secret-id` | `curl -X POST -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/approle/role/billing-app/secret-id \| jq .data` | Yangi `secret_id` va uning xavfsiz `secret_id_accessor` ini yaratadi. |
| **CREATE WRAPPED SECRET-ID (1-martalik shifrlangan quti)** | `vault write -wrap-ttl=120s -f auth/approle/role/billing-app/secret-id` | `curl -X POST -H "X-Vault-Token: $TOKEN" -H "X-Vault-Wrap-TTL: 120s" https://vault-srv.sarvartech.uz/v1/auth/approle/role/billing-app/secret-id \| jq .wrap_info.token` | 120 soniya yashovchi va faqat 1 marta ochiladigan shifrlangan `wrapping_token` beradi. |
| **UNWRAP (Qutini ochish)** | `vault unwrap <WRAPPING_TOKEN>` | `curl -X POST -H "X-Vault-Token: <WRAPPING_TOKEN>" https://vault-srv.sarvartech.uz/v1/sys/wrapping/unwrap \| jq .data` | Qutini ochib ichidagi asl `secret_id` ni oladi. |
| **LIST ACCESSORS (Secret-ID larni ko'rish)** | `vault list auth/approle/role/billing-app/secret-id` | `curl -X LIST -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/approle/role/billing-app/secret-id` | Ushbu rolda nechta aktiv `secret_id` borligini Accessor orqali sanaydi. |
| **DESTROY SECRET-ID (Parolni bekor qilish)** | `vault write auth/approle/role/billing-app/secret-id-accessor/destroy secret_id_accessor="<ACCESSOR>"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"secret_id_accessor": "<ACCESSOR>"}' https://vault-srv.sarvartech.uz/v1/auth/approle/role/billing-app/secret-id-accessor/destroy` | O'g'irlangan yoki eskirgan `secret_id` ni Accessor orqali bekor qiladi. |
| **LOGIN (AppRole bilan token olish)** | `vault write auth/approle/login role_id="<ROLE_ID>" secret_id="<SECRET_ID>"` | `curl -X POST -d '{"role_id": "<ROLE_ID>", "secret_id": "<SECRET_ID>"}' https://vault-srv.sarvartech.uz/v1/auth/approle/login \| jq -r .auth.client_token` | Servis Vault bilan bog'lanib o'zining vaqtinchalik `client_token` ini oladi. |

---

## 5. FOYDALANUVCHILAR (USERPASS & ADMIN) CRUD BOSHQARUVI

> Inson muhandislari va administratorlar hisoblarini boshqarish, yangi user qo'shish va ularni o'chirish (offboarding).

| Amal | CLI Buyrug'i | REST API (cURL) | Izoh / Natija |
| :--- | :--- | :--- | :--- |
| **AUTH ENABLE (Userpass yoqish)** | `vault auth enable userpass` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"type": "userpass"}' https://vault-srv.sarvartech.uz/v1/sys/auth/userpass` | Userpass autentifikatsiya tizimini yoqadi. |
| **CREATE ADMIN USER** | `vault write auth/userpass/users/sarvar_admin password="StrongPassword2026!" policies="admin"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"password": "StrongPassword2026!", "policies": "admin"}' https://vault-srv.sarvartech.uz/v1/auth/userpass/users/sarvar_admin` | **To'liq admin huquqli shaxsiy hisob** ochadi. |
| **CREATE DEV USER** | `vault write auth/userpass/users/junior_dev password="DevPass123!" policies="dev-policy"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"password": "DevPass123!", "policies": "dev-policy"}' https://vault-srv.sarvartech.uz/v1/auth/userpass/users/junior_dev` | Faqat o'ziga ajratilgan siyosatga ega dasturchi hisobini ochadi. |
| **READ USER (Ma'lumotlarini ko'rish)** | `vault read auth/userpass/users/sarvar_admin` | `curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/userpass/users/sarvar_admin \| jq .data` | Userning siyosatlari, token TTL va parametrlarini ko'rsatadi. |
| **LIST USERS (Userlar ro'yxati)** | `vault list auth/userpass/users` | `curl -X LIST -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/userpass/users` | Tizimdagi barcha faol inson hisoblari (username) ro'yxatini chiqaradi. |
| **UPDATE PASSWORD (Parolni yangilash)** | `vault write auth/userpass/users/sarvar_admin/password password="NewSecretPass2026!"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"password": "NewSecretPass2026!"}' https://vault-srv.sarvartech.uz/v1/auth/userpass/users/sarvar_admin/password` | Mavjud userning parolini zudlik bilan almashtiradi. |
| **UPDATE POLICIES (Siyosatni o'zgartirish)** | `vault write auth/userpass/users/junior_dev policies="dev-policy,qa-policy"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"policies": "dev-policy,qa-policy"}' https://vault-srv.sarvartech.uz/v1/auth/userpass/users/junior_dev` | Userning vakolatlarini kengaytiradi yoki qisqartiradi. |
| **DELETE / REMOVE USER (Userni o'chirish)** | `vault delete auth/userpass/users/junior_dev` | `curl -X DELETE -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/userpass/users/junior_dev` | **Userni tizimdan butunlay o'chiradi (Offboarding).** U endi login qila olmaydi. |
| **LOGIN AS USER (User sifatida kirish)** | `vault login -method=userpass username=sarvar_admin` | `curl -X POST -d '{"password": "StrongPassword2026!"}' https://vault-srv.sarvartech.uz/v1/auth/userpass/login/sarvar_admin \| jq -r .auth.client_token` | User o'z login va paroli bilan yangi faol token oladi. |

---

## 6. UNSEAL, SEAL, TOKENLAR & ACCESSOR BOSHQARUVI

> Server holati, shifrlash to'sig'i va foydalanuvchilar sessiyalari.

| Amal | CLI Buyrug'i | REST API (cURL) | Izoh / Natija |
| :--- | :--- | :--- | :--- |
| **STATUS (Holatni ko'rish)** | `vault status` | `curl -s https://vault-srv.sarvartech.uz/v1/sys/health \| jq .` | Server Sealed/Unsealed, HA Active/Standby, Version holatini ko'rsatadi. |
| **INIT (Birlamchi initsializatsiya)** | `vault operator init -key-shares=5 -key-threshold=3` | `curl -X POST -d '{"secret_shares": 5, "secret_threshold": 3}' https://vault-srv.sarvartech.uz/v1/sys/init` | Faqat 1 marta bajariladi! Unseal kalitlari va Root Tokenni generatsiya qiladi. |
| **UNSEAL (Muhrni ochish)** | `vault operator unseal <UNSEAL_KEY>` | `curl -X POST -d '{"key": "<UNSEAL_KEY>"}' https://vault-srv.sarvartech.uz/v1/sys/unseal` | Threshold to'lguncha 3 ta kalit kiritiladi va shifrlash to'sig'i ochiladi. |
| **SEAL (Favqulodda muhrlash)** | `vault operator seal` | `curl -X POST -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/sys/seal` | Kiberhujum vaqtida xotiradagi Master kalitni bir lahzada yo'q qilib serverni qulflaydi. |
| **CREATE TOKEN (Cheklangan token)** | `vault token create -ttl=2h -use-limit=1 -policy=billing-policy -orphan` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"ttl": "2h", "num_uses": 1, "policies": ["billing-policy"], "no_parent": true}' https://vault-srv.sarvartech.uz/v1/auth/token/create` | 2 soat yashovchi, faqat 1 marta ishlatiladigan xavfsiz token yaratadi. |
| **CREATE IP-BOUND TOKEN** | `vault token create -ttl=4h -policy=billing-policy -bound-cidrs="192.168.86.1/32"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"ttl": "4h", "bound_cidrs": ["192.168.86.1/32"]}' https://vault-srv.sarvartech.uz/v1/auth/token/create` | Faqat ko'rsatilgan IP manzildan kirishga ruxsat beruvchi token beradi. |
| **LOOKUP TOKEN (O'z tokenini tekshirish)** | `vault token lookup` | `curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/token/lookup-self \| jq .data` | Tokenning qolgan vaqti (TTL), ruxsatlari va accessorini ko'rsatadi. |
| **LOOKUP BY ACCESSOR (Tokenni bilmasdan ko'rish)** | `vault token lookup -accessor "<ACCESSOR>"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"accessor": "<ACCESSOR>"}' https://vault-srv.sarvartech.uz/v1/auth/token/lookup-accessor` | Admin dasturchi tokenini bilmasdan faqat uning accessorini tekshiradi. |
| **RENEW (Vaqtini uzaytirish)** | `vault token renew` | `curl -X POST -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/auth/token/renew-self` | Token muddati tugamasidan oldin uni uzaytiradi (Lease renewal). |
| **REVOKE (Tokenni bekor qilish)** | `vault token revoke <TOKEN>` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"token": "<TOKEN>"}' https://vault-srv.sarvartech.uz/v1/auth/token/revoke` | Tokenni va uning barcha bola tokenlarini zudlik bilan bekor qiladi. |
| **REVOKE BY ACCESSOR (Accessor orqali bekor qilish)** | `vault token revoke -accessor "<ACCESSOR>"` | `curl -X POST -H "X-Vault-Token: $TOKEN" -d '{"accessor": "<ACCESSOR>"}' https://vault-srv.sarvartech.uz/v1/auth/token/revoke-accessor` | **Eng xavfsiz bekor qilish usuli!** Tokenni o'zini bilmasdan kirishni to'xtatadi. |

---

## 6. ENG KO'P ISHLATILADIGAN 10 TA BUYRUQ

```bash
# 1. Server holatini tekshirish
vault status

# 2. Yangi secret qo'shish yoki yangilash
vault kv put secret/organizations/sarvartech/payment/prod db_pass="Kripto@Parol#2026"

# 3. Secretni terminalda o'qish
vault kv get secret/organizations/sarvartech/payment/prod

# 4. Secretni boshqa kalitlarni buzmasdan qisman yangilash
vault kv patch secret/organizations/sarvartech/payment/prod api_token="live_tok_991"

# 5. Dasturchiga 1 soatlik 1 martalik token yaratib berish
vault token create -ttl=1h -use-limit=1 -policy=developer-policy

# 6. Siyosatni fayldan yuklash
vault policy write payment-policy payment-policy.hcl

# 7. Accessor orqali tokenni darhol bekor qilish
vault token revoke -accessor "a6KNiBTnyMT..."

# 8. Real-time audit logni kuzatish (jq bilan)
tail -f /var/log/vault/vault_audit.log | jq '{time: .time, path: .request.path, ip: .request.remote_address}'

# 9. 1-klikda to'liq Raft zaxira nusxa (Snapshot) olish
vault operator raft snapshot save /backups/vault_$(date +%F).snap

# 10. Maxsus CLI boshqaruv konsolini ochish (SarvarTech)
vault-panel
```
