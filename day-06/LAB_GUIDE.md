# 🛠️ DAY 6: AMALIY QO'LLANMA (LAB GUIDE)
## Transit Engine Bilan Shifrlash va Kalitlarni Rotatsiya Qilish

Ushbu amaliyotda biz Transit engine'ni yoqamiz, yangi AES-256 shifrlash kaliti hosil qilamiz, ma'lumotlarni shifrlash va de-shifrlashni o'rganamiz, kalitni yangi versiyaga rotatsiya qilamiz.

---

### 1-Qadam: Transit Secret Engine'ni Yoqish

```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="<ROOT_TOKEN>"

# Transit engine'ni faollashtirish
vault secrets enable transit
```

---

### 2-Qadam: Shifrlash Kalitini Yaratish

Mijozlarning bank kartalari uchun `customer-cards` nomli yangi kalit yaratamiz:

```bash
vault write -f transit/keys/customer-cards

# Kalit ma'lumotlarini ko'rish
vault read transit/keys/customer-cards
```
> Ko'rib turganingizdek, kalit turi: `aes256-gcm96`, joriy versiya: `latest_version: 1`. Kalitning o'zi (private key) esa ekranga chiqmaydi, u Vault ichida muhrlangan.

---

### 3-Qadam: Ma'lumotni Shifrlash (Encryption)

Transit engine'ga ma'lumot yuborishda u **Base64** formatida bo'lishi talab qilinadi.

Keling, karta raqamini shifrlaymiz:
```bash
PLAINTEXT="8600 1234 5678 9012"
BASE64_TEXT=$(echo -n "$PLAINTEXT" | base64)

CIPHERTEXT=$(vault write -field=ciphertext transit/encrypt/customer-cards plaintext="$BASE64_TEXT")

echo "Shifrlangan natija: $CIPHERTEXT"
```
Natija quyidagicha bo'ladi:
`vault:v1:qweRtY987...==`

Ushbu satrni ma'lumotlar bazasiga bexavotir saqlash mumkin!

---

### 4-Qadam: Ma'lumotni De-shifrlash (Decryption)

Faqatgina tegishli ruxsati bor dastur ushbu shifrlangan matnni ochib o'qiy oladi:

```bash
DECRYPTED_BASE64=$(vault write -field=plaintext transit/decrypt/customer-cards ciphertext="$CIPHERTEXT")

ORIGINAL_TEXT=$(echo "$DECRYPTED_BASE64" | base64 --decode)

echo "Asl matn tiklandi: $ORIGINAL_TEXT"
```
✅ **Natija:** `8600 1234 5678 9012`

---

### 5-Qadam: Kalitni Rotatsiya Qilish (Key Rotation) va Rewrap

6 oydan so'ng xavfsizlik talabi bilan kalitni yangilaymiz:

```bash
# Kalitni yangi versiyaga aylantirish
vault write -f transit/keys/customer-cards/rotate

# Tekshiramiz
vault read -field=latest_version transit/keys/customer-cards
```
> Endi `latest_version: 2` bo'ldi!

Endi yangi shifrlangan ma'lumotlar `vault:v2:...` prefiksi bilan chiqadi.

#### Eski ma'lumotni v2 ga qayta o'rash (Rewrap):
```bash
NEW_CIPHERTEXT=$(vault write -field=ciphertext transit/rewrap/customer-cards ciphertext="$CIPHERTEXT")
echo "Yangi versiyaga o'ralgan shifr: $NEW_CIPHERTEXT"
```
Endi u `vault:v2:...` ga aylandi, eng muhimi — dasturchi kartaning asl raqamini ko'rishiga hojat qolmadi!

---

### 🎯 Day 6 Mini-Topshiriq:
1. `transit/keys/orders-hash` kalitini yarating va uning turini `ed25519` qiling.
2. Unga biror matn yuborib raqamli imzo (`transit/sign`) va imzoni tekshirish (`transit/verify`) amallarini bajaring.
