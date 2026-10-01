# 🛠️ DAY 3: AMALIY QO'LLANMA (LAB GUIDE)
## PostgreSQL Bilan Dinamik Sirlar (Database Engine) Amaliyoti

Ushbu amaliyotda biz PostgreSQL ma'lumotlar bazasiga Vault'ni ulaymiz, dinamik foydalanuvchi yaratish qoidasini (Role) belgilaymiz va bir marta ishlatiladigan vaqtinchalik hisoblar generatsiya qilamiz.

---

### 1-Qadam: Test Uchun PostgreSQL O'rnatish

Agar serveringizda PostgreSQL bo'lmasa, uni tezda o'rnatib olamiz:

```bash
sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib

# PostgreSQL xizmatini yoqish
sudo systemctl enable --now postgresql

# Vault uchun maxsus ma'muriy hisob va test baza ochish
sudo -u postgres psql -c "CREATE USER vault_admin WITH SUPERUSER PASSWORD 'VaultAdminSecretPass123!';"
sudo -u postgres psql -c "CREATE DATABASE shop_db;"
```

---

### 2-Qadam: Database Secrets Engine'ni Yoqish

```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="<ROOT_TOKEN>"

# Database engine'ni yoqish
vault secrets enable database
```

---

### 3-Qadam: Vault'ni PostgreSQL Bazasiga Bog'lash

Vault bazaga yangi foydalanuvchilar qo'sha olishi uchun u bilan aloqa o'rnatishi kerak:

```bash
vault write database/config/my-postgres-db \
    plugin_name=postgresql-database-plugin \
    allowed_roles="readonly-role" \
    connection_url="postgresql://{{username}}:{{password}}@127.0.0.1:5432/shop_db?sslmode=disable" \
    username="vault_admin" \
    password="VaultAdminSecretPass123!"
```

---

### 4-Qadam: Dinamik Rol Yaratish (Creation Statements)

Endi har safar yangi sir so'ralganda Vault bazada qanday SQL buyruqlarini bajarishi kerakligini belgilaymiz:

```bash
vault write database/roles/readonly-role \
    db_name=my-postgres-db \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
```

* `{{name}}`: Vault o'zi avtomatik generatsiya qiladigan unikal username (`v-token-readonly-...`).
* `{{password}}`: Tasodifiy kuchli parol.
* `{{expiration}}`: 1 soatdan keyingi vaqt.
* `default_ttl="1h"`: Standart amal qilish muddati — 1 soat.

---

### 5-Qadam: Dinamik Foydalanuvchi Yaratish va Tekshirish

Endi dastur nomidan yangi parol so'raymiz:

```bash
vault read database/creds/readonly-role
```

Quyidagi kabi javob qaytadi:
```text
Key                Value
---                -----
lease_id           database/creds/readonly-role/h73a11b6...
lease_duration     1h
lease_renewable    true
password           A1a-8FzQv_k...
username           v-token-readonly-r01a8f...
```

#### PostgreSQL'da tekshiramiz:
```bash
sudo -u postgres psql -c "\du"
```
Haqiqatda ham bazada yangi `v-token-readonly-...` foydalanuvchisi paydo bo'lganini ko'rasiz!

---

### 6-Qadam: Favqulodda Bekor Qilish (Revocation)

Dastur o'z ishini tugatdi yoki uning paroli sizib chiqdi deb tasavvur qilaylik. Kutib o'tirmasdan, lease ID orqali parolni darhol bekor qilamiz:

```bash
vault lease revoke database/creds/readonly-role/<SIZNING_LEASE_ID'INGIZ>
```

Yana bazadagi foydalanuvchilarni tekshiring:
```bash
sudo -u postgres psql -c "\du"
```
🎉 Foydalanuvchi PostgreSQL'dan **butunlay o'chirilgan!** Hech qanday qo'lda ish bajarilmadi.

---

### 🎯 Day 3 Mini-Topshiriq:
1. `default_ttl="2m"` (2 daqiqa) qilib yangi `quick-test-role` yarating.
2. Undan yangi login oling va PostgreSQL'da paydo bo'lganini ko'ring.
3. Hech narsa qilmasdan 2 daqiqa kuting, so'ng yana `\du` qilib, Vault 2 daqiqadan so'ng uni o'zi o'chirib tashlaganiga guvoh bo'ling.
