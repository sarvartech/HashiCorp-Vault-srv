# 📚 DAY 2: MA'RUZA MATNI
## Key-Value (KV) Secrets Engine: Versiyalash, Metadata va REST API

---

### 1. Secret Engines Kontseptsiyasi

Vault'da barcha ma'lumotlar **Secret Engine**lar orqali boshqariladi.
Har bir Secret Engine ma'lum bir URL yo'liga (path) ulanadi (mount qilinadi):
* `secret/` yoki `kv/` -> Key-Value saqlash
* `database/` -> Dinamik bazalar
* `pki/` -> Sertifikatlar

Vault'ning go'zalligi shundaki, siz bitta turdagi engine'ni bir nechta turli yo'llarga ulashingiz mumkin (masalan: `secret/dev/`, `secret/prod/`, `secret/finance/`).

---

### 2. KV Version 1 va KV Version 2 Farqi

Key-Value (KV) Vault'dagi eng ko'p ishlatiladigan engine hisoblanadi. Uning 2 ta versiyasi mavjud:

| Xususiyat | KV Version 1 | KV Version 2 (Tavsiya etiladi) |
| :--- | :--- | :--- |
| **Versiyalash** | Yo'q (har doim ustidan yoziladi) | **Bor** (har bir o'zgarish yangi versiya bo'ladi) |
| **Metadata** | Yo'q | **Bor** (yaratilgan vaqt, kim yozgani, o'chirilganligi) |
| **Soft Delete** | Yo'q (darhol o'chadi) | **Bor** (belgilangan versiyani o'chirish va tiklash mumkin) |
| **Check-and-Set (CAS)**| Yo'q | **Bor** (bir vaqtning o'zida yozilganda kesh to'qnashuvini oldini oladi) |
| **API Path tuzilishi** | `secret/<path>` | `secret/data/<path>` (ma'lumot uchun)<br>`secret/metadata/<path>` (tarix uchun) |

---

### 3. KV-v2 Ma'lumotlar Modeli

KV-v2 da har bir sir 2 qismdan iborat:

```
                      ┌───────────────────────┐
                      │   secret/app/config   │
                      └───────────┬───────────┘
                                  │
          ┌───────────────────────┴───────────────────────┐
          ▼                                               ▼
┌──────────────────┐                            ┌──────────────────┐
│     METADATA     │                            │   DATA VERSIONS  │
├──────────────────┤                            ├──────────────────┤
│ created_time     │                            │ v1: db_pass=abc  │
│ max_versions: 10 │                            │ v2: db_pass=xyz  │
│ current_ver: 3   │                            │ v3: db_pass=123  │ (active)
└──────────────────┘                            └──────────────────┘
```

1. **Active Data:** Joriy faol versiya. Agar dastur versiyani ko'rsatmasa, doim eng oxirgi faol versiya qaytariladi.
2. **Soft Delete (`delete`):** Versiya o'chirilgan deb belgilanadi (`destroyed: false`, `deletion_time: timestamp`), lekin xohlagan payt **undelete** qilish mumkin.
3. **Hard Destroy (`destroy`):** Ushbu versiyaning ma'lumoti butunlay yo'q qilinadi va qayta tiklab bo'lmaydi.

---

### 4. REST API Bilan Bog'lanish Arxitekturasi

CLI'dagi barcha buyruqlar aslida orqa fonda oddiy HTTP REST so'rovlarini yuboradi:
* `GET /v1/secret/data/my-secret` — Sirni o'qish
* `POST /v1/secret/data/my-secret` — Yangi versiya yozish
* `POST /v1/secret/delete/my-secret` — Versiyani soft-delete qilish
* `POST /v1/secret/undelete/my-secret` — Qayta tiklash
* `POST /v1/secret/destroy/my-secret` — Butunlay yo'q qilish

Har bir HTTP so'rovida `X-Vault-Token: <token>` sarlavhasi (header) yuboriladi.
