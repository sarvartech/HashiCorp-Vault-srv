# 🛠️ DAY 2: AMALIY QO'LLANMA (LAB GUIDE)
## KV-v2 Secret Engine: CLI va REST API Amaliyoti

Ushbu amaliyotda siz KV-v2 engine'ni yoqasiz, bir nechta sir versiyalarini yaratasiz, versiyalarni boshqarasiz, o'chirilgan sirni tiklaysiz va `curl` orqali to'g'ridan-to'g'ri REST API bilan ishlaysiz.

---

### 1-Qadam: KV-v2 Secret Engine'ni Yoqish

Terminalda avvalo Vault token va manzilni sozlang:
```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="<SIZNING_ROOT_TOKENINGIZ>"
```

Endi `secret/` yo'liga KV-v2 engine'ni ulaymiz:
```bash
# Mavjud engine'larni ko'rish
vault secrets list

# KV-v2 ni secret/ yo'liga ulash
vault secrets enable -path=secret kv-v2

# Muvaffaqiyatli ulanganini tekshirish
vault secrets list -detailed
```

---

### 2-Qadam: Birinchi Sirni Yaratish (Version 1)

Keling, ishlab chiqarish (production) ma'lumotlar bazasi konfiguratsiyasini saqlaymiz:

```bash
vault kv put secret/production/database \
    host="192.168.0.50" \
    port="5432" \
    username="db_admin" \
    password="SuperSecretPassword2026!"
```

Sirni o'qib ko'rish:
```bash
vault kv get secret/production/database
```
> Chiqishda `version: 1` va kiritilgan ma'lumotlar paydo bo'ladi.

Faqatgina ma'lum bir maydonni (masalan faqat parolni) chiqarish:
```bash
vault kv get -field=password secret/production/database
```

---

### 3-Qadam: Versiyalash Imkoniyatini Sinash (Version 2)

Ma'lumotlar bazasi paroli yangilandi deylik:
```bash
vault kv patch secret/production/database password="NewRotatedPassword999!"
```
*(Eslatma: `put` butun kalitlarni almashtiradi, `patch` esa faqat ko'rsatilgan maydonni yangilab yangi versiya qiladi).*

Endi tekshiramiz:
```bash
vault kv get secret/production/database
```
> Endi `version: 2` ko'rsatiladi!

#### Eski (1-versiyadagi) parolni qanday o'qiymiz?
```bash
vault kv get -version=1 secret/production/database
```
Tarix (Metadata) ma'lumotlarini ko'rish:
```bash
vault kv metadata get secret/production/database
```

---

### 4-Qadam: Soft Delete va Undelete Jarayoni

Tasodifan 2-versiyani o'chirib yubordik:
```bash
vault kv delete -versions=2 secret/production/database
```

Endi o'qib ko'ramiz:
```bash
vault kv get secret/production/database
```
> Natija: `deletion_time` ko'rsatiladi, ma'lumot ko'rinmaydi.

Lekin bu ma'lumot butunlay yo'qolmagan! Uni qayta tiklaymiz:
```bash
vault kv undelete -versions=2 secret/production/database
vault kv get secret/production/database
```
> Ma'lumot yana to'liq tiklandi!

Agar butunlay qaytarib bo'lmas qilib yo'q qilmoqchi bo'lsak:
```bash
# Ehtiyot bo'ling: bu qaytarilmaydi!
vault kv destroy -versions=1 secret/production/database
```

---

### 5-Qadam: REST API (`curl`) orqali Boshqarish

Vault faqat CLI emas, balki REST API orqali ham to'liq boshqariladi.

#### 1. API orqali yangi sir yozish:
```bash
curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
     --request POST \
     --data '{"data": {"api_key": "sk-live-123456789", "env": "prod"}}' \
     http://127.0.0.1:8200/v1/secret/data/payments/stripe | jq
```

#### 2. API orqali sirni o'qish:
```bash
curl -s --header "X-Vault-Token: $VAULT_TOKEN" \
     http://127.0.0.1:8200/v1/secret/data/payments/stripe | jq .data.data
```

---

### 🎯 Day 2 Mini-Topshiriq:
1. `secret/dev/frontend` manzilida `NODE_ENV=development` va `API_URL=http://localhost:3000` sirlarini saqlang.
2. Unga yangi `SENTRY_DSN` maydonini qo'shib, 2-versiyani hosil qiling.
3. Metadata buyrug'i orqali ikkala versiyaning yaratilgan vaqtini solishtiring.
