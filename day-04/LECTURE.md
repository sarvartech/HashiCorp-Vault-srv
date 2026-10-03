# 📚 DAY 4: MA'RUZA MATNI
## Autentifikatsiya Usullari (Auth Methods) va HCL Ruxsat Siyosatlari (Policies)

---

### 1. Insonlar va Mashinalar Uchun Autentifikatsiya

Vault'ga kim kirmoqda? U 2 toifaga bo'linadi:

1. **Insonlar (Human Identity):**
   * `userpass` — Oddiy login va parol (test muhitlar uchun).
   * `ldap` / `active_directory` — Korporativ domen hisoblari.
   * `oidc` / `github` / `okta` — SSO (Single Sign-On).

2. **Dasturlar va Mashinalar (Machine Identity):**
   * `approle` — Mikroservislar, backend ilovalar, CI/CD pipeline'lar uchun sanoat standarti.
   * `kubernetes` — K8s ServiceAccount tokenlari orqali podlarni avtorizatsiya qilish.
   * `aws` / `azure` / `gcp` — Cloud IAM instansiyalari uchun.
   * `cert` — TLS Client Certificate (mTLS) orqali kirish.

---

### 2. AppRole Qanday Ishlaydi?

AppRole — xuddi insonlardagi `username` va `password` kabi, lekin mashinalar uchun optimallashgan:
* **Role ID:** Ochiq ID (Username o'rnida). Kodga yoki konfiguratsiyaga qo'yish xavfsiz.
* **Secret ID:** Juda maxfiy kalit (Parol o'rnida). CI/CD paytida yoki xavfsiz kanallar orqali faqat bitta mashinaga yetkaziladi.

```
┌─────────────────────────────────┐
│     Backend App / CI Runner     │
└────────────────┬────────────────┘
                 │ 1. POST /v1/auth/approle/login
                 │    { "role_id": "...", "secret_id": "..." }
                 ▼
        ┌─────────────────┐
        │   VAULT CORE    │
        └────────┬────────┘
                 │ 2. Agar to'g'ri bo'lsa:
                 │    - Qisqa muddatli Token (masalan 1 soat)
                 │    - Biriktirilgan Policy (ruxsatnomalar)
                 ▼
┌─────────────────────────────────┐
│ Token qaytadi: "hvs.CAES..."    │ ── 3. Shu token bilan sirlarni o'qiydi
└─────────────────────────────────┘
```

---

### 3. HCL (HashiCorp Configuration Language) Policies

Vault'da barcha ruxsatlar **Default Deny (standart bo'yicha hamma narsa taqiqlangan)** printsipida ishlaydi. Agar aniq ruxsat beruvchi siyosat yozilmasa, foydalanuvchi hech narsani o'qiy olmaydi.

#### Path turlari:
* `path "secret/data/dev/*"` — `dev/` ostidagi barcha sirlarga taalluqli.
* `path "secret/data/production/database"` — Aniq bitta sirga taalluqli.
* `path "secret/data/+/config"` — Istalgan 1 ta oraliq papkaga mos keladi (`dev/config`, `test/config`).

#### Imkoniyatlar (Capabilities):
* `create` — Yangi ma'lumot yaratish.
* `read` — Ma'lumotni o'qish.
* `update` — Mavjud ma'lumotni o'zgartirish.
* `delete` — O'chirish.
* `list` — Papka ichidagi ro'yxatni ko'rish.
* `deny` — Ruxsatni qat'iy taqiqlash (hatto boshqa joyda ruxsat berilgan bo'lsa ham ustun turadi).

#### Siyosat Namunasi:
```hcl
# Faqat o'qish ruxsati
path "secret/data/production/*" {
  capabilities = ["read"]
}

# Ham o'qish, ham yozish ruxsati
path "secret/data/staging/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Xavfsizlik bo'limi kalitlariga qat'iyan yo'latmaslik
path "secret/data/security/*" {
  capabilities = ["deny"]
}
```

---

### 4. Foydalanuvchilarni Boshqarish (User Management & Lifecycle)

Vault'da inson muhandislari uchun alohida shaxsiy hisoblar ochish xavfsizlikning eng birinchi talabi hisoblanadi.

#### Nima uchun umumiy Root Token ishlatilmasligi kerak?
1. **Shaxsiy javobgarlik (Audit Trail):** Agar hamma Root token ishlatsa, audit loglarida kim qaysi parolni o'zgartirganini yoki o'chirganini bilib bo'lmaydi.
2. **Eng kam imtiyoz printsipi (Least Privilege):** Har bir xodimga faqat o'ziga kerakli hududga ruxsat beriladi.
3. **Hisobni o'chirish (Offboarding):** Xodim ishdan ketganda, uning hisobi darhol o'chiriladi va barcha faol tokenlari bekor qilinadi.

#### Foydalanuvchi Hayot Sikli (User Lifecycle):
* **Yangi user / admin yaratish:** `vault write auth/userpass/users/<username> password="..." policies="..."`
* **Ro'yxatni ko'rish (List):** `vault list auth/userpass/users`
* **Parolni yoki siyosatni yangilash (Update):** Yangi parametrlar bilan qayta `write` qilinadi.
* **Foydalanuvchini o'chirish (Remove / Delete):** `vault delete auth/userpass/users/<username>`
* **Tokenlarini bekor qilish (Revoke):** O'chirilgach, uning ilgari olgan va hali eskirib ulgurmagan faol tokenlari ham `vault token revoke -accessor` orqali bekor qilinadi.

