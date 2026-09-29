# 🛡️ HASHICORP VAULT ENTERPRISE: ARCHITECTURE, INTERNALS & PRODUCTION MASTER GUIDE
> **"0 dan To'liq Production Administratorlikkacha: Xavfsizlik Arxitekturasi, Ichki Mexanizmlar, Terminlar Mantig'i va Zamonaviy Muhandislik Amaliyoti"**

[![Vault Version](https://img.shields.io/badge/Vault-v1.15%2B%20Enterprise-blue.svg)](https://www.vaultproject.io/)
[![Zero Trust](https://img.shields.io/badge/Security-Zero--Trust%20Bank--Grade-emerald.svg)]()
[![Production Domain](https://img.shields.io/badge/Domain-vault--srv.sarvartech.uz-indigo.svg)](https://vault-srv.sarvartech.uz)
[![Storage](https://img.shields.io/badge/Storage-Integrated%20Raft-red.svg)]()
[![License](https://img.shields.io/badge/License-MIT-orange.svg)]()

---

## 📑 MUNDARIJA (TABLE OF CONTENTS)
1. [Kirish: Nega Zamonaviy Dunyoga Vault Kerak? (Secret Sprawl Muammosi)](#1-kirish-nega-zamonaviy-dunyoga-vault-kerak)
2. [Vault Qanday Ishlaydi? Asosiy Ishlash Prinsipi va Topologiyasi](#2-vault-qanday-ishlaydi-asosiy-ishlash-prinsipi)
3. [Har Bir Terminning Chuqur Mantig'i va Mexanizmlar Foydasi](#3-har-bir-terminning-chuqur-mantigi)
4. [Enterprise Daraxt Modeli (Production Tree Hierarchy)](#4-enterprise-daraxt-modeli)
5. [O'rnatishdan Tortib Productiongacha: To'liq Yo'l Xaritasi](#5-ornatishdan-tortib-productiongacha-to'liq-yol)
6. [Hozirgi Yangi Muhandislar (DevOps/DevSecOps) Vaultni Qanday Ishlatmoqda?](#6-zamonaviy-muhandislar-vaultni-qanday-ishlatmoqda)
7. [SarvarTech Infratuzilmasi: Maxsus Ishlab Chiqilgan Boshqaruv Asboblari](#7-sarvartech-infratuzilmasi-asboblari)
8. [Administratorning 5 Ta Qat'iy Taqiqlangan Xatosi](#8-administratorning-5-ta-taqiqlangan-xatosi)
9. [Xulosa va Keyingi Qadamlar](#9-xulosa)
10. ⚡ **[Vault CRUD & Operator Cheat Sheet (Alohida Sahifa)](VAULT_CRUD_CHEATSHEET.md)**

---

## 1. KIRISH: NEGA ZAMONAVIY DUNYOGA VAULT KERAK?

Axborot xavfsizligida eng katta zaiflik bu — **inson omili** va **tarqoq parollar (Secret Sprawl)** muammosidir.

### ❌ An'anaviy Usullarning Halokati:
* **Statik `.env` fayllar:** Dasturchi `.env` faylida bazaning login/parolini saqlaydi. Serverga kirgan har qanday odam uni o'qiy oladi.
* **Git Repository Leak:** Ochiq yoki yopiq GitHub/GitLab repozitoriyalariga adashib maxfiy API kalitlar push qilinadi. Dunyo bo'ylab har kuni minglab AWS, Telegram bot va DB tokenlari shu tariqa xakerlar qo'liga tushadi.
* **Hardcoded Credentials:** Dastur kodining ichiga yozilgan parollar. Bitta parolni o'zgartirish uchun 20 ta mikroservisni qayta yurgizish (rebuild & redeploy) talab etiladi.
* **Nazoratsiz Ruxsatlar:** Ishdan ketgan xodim o'zi bilgan parollardan foydalanib tizimga kirmasligiga hech qanday kafolat yo'q.

### 🛡️ HashiCorp Vault Taqdim Etadigan Yechim (Zero-Trust):
Vault — bu shunchaki "parol saqlaydigan baza" emas. Bu **Zero-Trust (Hech kimga ishonma)** falsafasiga asoslangan **Kriptografik Boshqaruv Platformasi**dir:
1. **Yagona Haqiqat Manbai (Single Source of Truth):** Barcha tizim kalitlari bir joyda shifrlangan holatda saqlanadi.
2. **Vaqtinchalik Kalitlar (Lease & TTL):** Hech bir ilova doimiy parolga ega bo'lmaydi. Kalitlar muddati (masalan, 1 soat) tugagach avtomatik o'chiriladi.
3. **To'liq Nazorat (Audit Logging):** Kim, qachon, qaysi IP manzildan qaysi secretni ko'rgani sekundigacha muhrlanadi.

---

## 2. VAULT QANDAY ISHLAYDI? ASOSIY ISHLASH PRINSIPI

Vault tizimi qat'iy **qatlamli xavfsizlik (Defense-in-Depth)** modeliga qurilgan. Har bir kelgan so'rov quyidagi bosqichlardan o'tadi:

```text
               [ CLIENT / DASTURCHI / MIKROSERVIS / CI-CD ]
                                    │
                                    │ 1. HTTPS So'rov (Token / Role-ID bilan)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             NGINX REVERSE PROXY & TLS (443)             │
       │               https://vault-srv.sarvartech.uz           │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼ (127.0.0.1:8200)
       ┌─────────────────────────────────────────────────────────┐
       │                     HTTP/REST API                       │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                  AUTHENTICATION (AUTH)                  │
       │    (Token, AppRole, Userpass, LDAP, OIDC tekshiruvi)    │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                    POLICY ENGINE (ACL)                  │
       │        (So'rov qilingan yo'lga ruxsat bormi? Deny/Allow)│
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             ENCRYPTION BARRIER (AES-GCM-256)            │
       │         (Xotiradagi Master Key orqali shifrlash)        │
       └──────┬─────────────────────┼─────────────────────┬──────┘
              │                     │                     │
              ▼                     ▼                     ▼
       ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
       │ AUTH METHODS │      │SECRETS ENGINE│      │AUDIT DEVICES │
       │ (AppRole,    │      │(KV v2, PKI,  │      │(Fayl, Syslog)│
       │  Token...)   │      │ Database...) │      │ (Fail-Closed)│
       └──────────────┘      └──────────────┘      └──────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             STORAGE BACKEND (INTEGRATED RAFT)           │
       │       (Diskda faqat 100% shifrlangan payload saqlanadi) │
       └─────────────────────────────────────────────────────────┘
```

### So'rovning O'tish Bosqichlari:
1. **Kirish (Auth):** Mijoz o'zini tanishtiradi (masalan, AppRole yoki Token orqali).
2. **Huquqni Tekshirish (Policy Check):** ACL tizimi mijozning ushbu yo'lga (`secret/data/...`) ruxsati bor-yo'qligini tekshiradi.
3. **Audit Log Muhrlash:** So'rov amalga oshishidan oldin u audit logga yoziladi.
4. **Shifrlash To'sig'i (Encryption Barrier):** Storage Backend dan olingan ma'lumot shifrdan chiqarilib, mijozga xavfsiz JSON ko'rinishida qaytariladi.

---

## 3. HAR BIR TERMINNING CHUQUR MANTIG'I

Vaultni professional boshqarish uchun uning fundamental terminlarini tushunish shart:

### 1. Encryption Barrier (Shifrlash To'sig'i)
* **Mantig'i:** Vaultning ichki xotirasi bilan tashqi disk (Storage) o'rtasidagi eng asosiy himoya devori.
* **Qanday ishlaydi?** Diskka yoziladigan har bir bayt **AES-GCM-256** simmetrik algoritmi orqali shifrlanadi.
* **Foydasi:** Agar server buzilsa, klonlansa yoki qattiq disk (SSD) jismonan o'g'irlab ketilsa ham, xaker diskdagi bitta ham parolni o'qiy olmaydi.

### 2. Memory Locking (`mlock`)
* **Mantig'i:** Linux operatsion tizimi xotira (RAM) yetishmay qolganda, operativ xotiradagi ma'lumotlarni qattiq diskdagi SWAP faylga chiqarib turadi.
* **Qanday ishlaydi?** `mlock()` tizim chaqiruvi yordamida Vault o'ziga ajratilgan RAM sahifalarini "muzlatib" qo'yadi.
* **Foydasi:** Vaultning xotiradagi ochilgan Master kalitlari va parollari hech qachon diskdagi SWAP ga yozilmaydi. Shuningdek disk dump qilinganda parollar fosh bo'lmaydi.

### 3. Shamir's Secret Sharing (Shamirning Maxfiy Taqsimoti)
* **Mantig'i:** Nega 1 ta bosh administrator butun bank kalitiga egalik qilmasligi kerak?
* **Matematik formulasi:** Master Key $N$ ta kalit bo'lagiga (Key Shares) bo'linadi. Uni qayta yig'ish uchun minimal $T$ ta kalit (Threshold) talab qilinadi.
  * Masalan: **Shares = 5, Threshold = 3**.
  * Bosh admin, Xavfsizlik xizmati rahbari, Server muhandisi — kamida 3 kishi bir vaqtda o'z kalitini kiritmaguncha tizim ochilmaydi.
* **Foydasi:** Insayderlik, xiyonat yoki bitta odamning parolini o'g'irlash orqali tizimni egallashning oldi olinadi.

### 4. Sealed vs Unsealed Holatlar
* **Sealed (Muhrlangan):** Server ishlayapti, lekin xotiradagi shifrlovchi Master Key yo'q qilingan. Vault har qanday so'rovga "503 Service Unavailable / Vault is sealed" deb javob beradi.
* **Unsealed (Ochiq):** Threshold kalitlari kiritilib, shifrlash to'sig'i ochilgan va operatsiyalar bajarilayotgan holat.
* **Auto-Unseal:** Har safar server reboot bo'lganda 3 ta odamni qidirib yurmaslik uchun AWS KMS, GCP KMS yoki loyihangizdagi kabi `vault-auto-unseal.service` orqali avtomatik muhrdan chiqarish mexanizmi.

### 5. Storage Backend va Integrated Raft Consensus
* **Mantig'i:** Vault o'z ma'lumotlarini qayerda saqlaydi?
* **Raft nima?** HashiCorp Vault o'zining ichiga o'rnatilgan **Raft Consensus Engine** ga ega.
* **Qanday ishlaydi?** 3 yoki 5 ta tugundan iborat klaster tuziladi. Ular orasidan 1 ta **Leader** saylanadi. Barcha ma'lumotlar kvorum ($N/2 + 1$) asosida tugunlarga ko'paytiriladi (replicate qilinadi).
* **Foydasi:** Qo'shimcha MySQL yoki Consul o'rnatish shart emas. Bitta server o'chib qolsa, boshqa tugun 1 soniyada Leaderlikni o'z qo'liga oladi (High Availability).

### 6. KV Secrets Engine: v1 vs v2
* **KV v1:** Versiyalash yo'q. Eski qiymat ustiga yangi yozilsa, eski parol yo'qoladi.
* **KV v2 (Production Standart):**
  * **Versioning:** Har safar yangilaganda v1, v2, v3 bo'lib saqlanadi.
  * **Soft-delete (`delete`):** Versiya vaqtincha yashiriladi, lekin kerak bo'lsa `undelete` orqali tiklanadi.
  * **Hard-destroy (`destroy`):** Kalit butunlay jismonan yo'q qilinadi.
  * **Check-and-Set (CAS):** Bir vaqtda 2 kishi tahrirlaganda bir-birining qiymatini buzib qo'yishdan himoya (Race condition prevention).

### 7. Tokenlar Anatomiyasi, TTL va Accessor
* **Service Token:** Standart token, ota-bola daraxtiga ega.
* **Batch Token:** Xotirada saqlanmaydi (stateless), juda yuqori yuklamali API lar uchun.
* **Orphan Token:** Otasi yo'q token. Uni yaratgan dasturchi ishdan ketib, uning akkaunti revoke bo'lsa ham, bu token o'chib qolmaydi (Servislar to'xtab qolmasligi uchun).
* **TTL va Lease:** Har bir token ma'lum vaqt (masalan, 1 soat) yashaydi. Dastur uni vaqti-vaqti bilan `renew` qilib turishi shart.
* **Token Accessor siri:**
  * Har bir token yaratilganda unga qo'shaloq **Accessor ID** beriladi.
  * Masalan: Token: `hvs.CAESII...` (Maxfiy), Accessor: `a6KNiBTny...` (Ochiq).
  * Administrator hech qachon dasturchining tokenini bilishi shart emas. Agar dasturchi noutbukini yo'qotsa, admin uning tokenni Accessor orqali bekor (revoke) qilib tashlaydi.

### 8. AppRole Mexanizmi va Response Wrapping
* **Inson omilisiz xavfsizlik (Machine-to-Machine):**
  * Mikroservis qanday qilib parolsiz Vaultga kiradi?
  * **Role-ID:** Servisning "Logini" (Ochiq holda configda turishi mumkin).
  * **Secret-ID:** Servisning "Paroli" (Juda maxfiy, faqat ilovaga beriladi).
* **Response Wrapping (Cubbyhole):**
  * CI/CD server `secret_id` ni mikroservisga yuborishda uni ochiq jo'natmaydi.
  * Vault uni 120 soniyalik shifrlangan 1-martalik qutiga solib beradi (`wrapping_token`).
  * Mikroservis uni ochib oladi (`unwrap`). Agar yo'lda xaker uni ochishga uringan bo'lsa — haqiqiy ilova "Token allaqachon ishlatilgan!" degan signal oladi va kiberhujum fosh bo'ladi.

### 9. Dinamik Database Parollari (Dynamic Secrets)
* **Mantig'i:** Nega ilova ma'lumotlar bazasining doimiy parolini bilmasligi kerak?
* **Qanday ishlaydi?**
  1. Backend ilova start oladi va Vaultga so'rov yuboradi.
  2. Vault PostgreSQL/MySQL da yangi user yaratadi: `v-approle-billing-a89f2` va unga 24 belgili kuchli parol generatsiya qiladi.
  3. Unga faqat 1 soat umr beradi (`TTL = 1h`).
  4. 1 soat o'tgach, ilova tokenni yangilamasa — Vault ushbu userni bazadan jismonan o'chirib yuboradi (`DROP USER`).

### 10. Transit Engine: Encryption as a Service (EaaS)
* **Mantig'i:** Dasturchilar o'zlari shifrlash algoritmini (AES, RSA) noto'g'ri implementatsiya qilib xatoga yo'l qo'yishadi.
* **Qanday ishlaydi?**
  * Ma'lumot Vaultda saqlanmaydi!
  * Ilova mijozning pasport seriyasini Vaultga yuboradi.
  * Vault uni AES-GCM bilan shifrlab qaytaradi: `vault:v1:98fa...`.
  * Ilova o'z bazasida faqat shu shifrlangan satrni saqlaydi.
  * Kerak bo'lganda Vaultga jo'natib shifrni yechtirib oladi (`decrypt`).

### 11. Fail-Closed Audit Logging
* **Bank darajasidagi eng qat'iy tamoyil:**
  * Agar audit qurilmasi (Fayl yoki Syslog) to'lib qolsa yoki ishlamay qolsa — **Vault barcha so'rovlarni qabul qilishni darhol to'xtatadi!**
  * *"Auditga yozilmagan harakat — sodir bo'lishi mumkin emas!"*
* **HMAC-SHA256 Xeshirlash:** Audit logga parollar ochiq matnda tushmaydi, barchasi bir tomonlama xeshlanadi.

---

## 4. ENTERPRISE DARAXT MODELI (PRODUCTION TREE HIERARCHY)

Tashkilotingizda yuzlab mikroservislar bo'lganda parollarni tartibli saqlash uchun quyidagi ko'p tashkilotli (**Multi-tenant**) iyerarxiya joriy qilingan:

```text
secret/
└── data/
    └── organizations/
        ├── sarvartech/
        │   ├── payment-service/
        │   │   ├── prod   --> { db_host, db_user, db_pass, api_key }
        │   │   ├── stage  --> { ... }
        │   │   └── dev    --> { ... }
        │   ├── mobile-banking-api/
        │   │   └── prod
        │   └── notification-service/
        │       └── prod
        └── partner-bank/
            └── core-service/
                └── prod
```

### Ushbu Modelning Yutuqlari:
1. **1 Qatorli ACL Siyosat:** Butun bir filial yoki loyihaga ruxsat berish uchun shunchaki:
   ```hcl
   path "secret/data/organizations/sarvartech/*" {
     capabilities = ["read", "list"]
   }
   ```
2. **Atrof-muhitlar (Environments) mustaqilligi:** Dasturchi adashib `dev` o'rniga `prod` parolini ololmaydi.

---

## 5. O'RNATISHDAN TORTIB PRODUCTIONGACHA: TO'LIQ YO'L

### 1-QADAM: Linux Server Tayyorlash va O'rnatish
```bash
# HashiCorp rasmiy GPG kaliti va reposini ulash (Ubuntu/Debian)
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install -y vault nginx jq
```

### 2-QADAM: Production Konfiguratsiyasi (`/etc/vault.d/vault.hcl`)
```hcl
# Integrated Raft Storage
storage "raft" {
  path    = "/opt/vault/data"
  node_id = "vault-node-1"
}

# TCP Listener (Localhost, tashqi oqim Nginx orqali keladi)
listener "tcp" {
  address       = "127.0.0.1:8200"
  tls_disable   = 1
}

# Web UI faollashtirish
ui = true

# Memory locking faol
disable_mlock = false

api_addr     = "https://vault-srv.sarvartech.uz"
cluster_addr = "https://127.0.0.1:8201"
```

### 3-QADAM: Systemd va Linux Huquqlari
```bash
sudo useradd --system --home /etc/vault.d --shell /bin/false vault
sudo chown -R vault:vault /opt/vault/data /etc/vault.d
sudo setcap cap_ipc_lock=+ep /usr/bin/vault

sudo systemctl daemon-reload
sudo systemctl enable --now vault
```

### 4-QADAM: Initsializatsiya va Unseal
```bash
export VAULT_ADDR="http://127.0.0.1:8200"
vault operator init -key-shares=5 -key-threshold=3
```
Chiqgan 5 ta Unseal kalit va 1 ta Initial Root Tokenni xavfsiz joyga oling. So'ngra muhrni oching:
```bash
vault operator unseal <KEY_1>
vault operator unseal <KEY_2>
vault operator unseal <KEY_3>
```

### 5-QADAM: Nginx Reverse Proxy va SSL (HTTPS)
`/etc/nginx/sites-available/vault.conf`:
```nginx
server {
    listen 80;
    server_name vault-srv.sarvartech.uz;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name vault-srv.sarvartech.uz;

    ssl_certificate     /etc/ssl/certs/vault.crt;
    ssl_certificate_key /etc/ssl/private/vault.key;

    # Vault Core API & UI
    location / {
        proxy_pass http://127.0.0.1:8200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_address;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # Vault Management Web Console
    location /app/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_address;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 6. ZAMONAVIY MUHANDISLAR VAULTNI QANDAY ISHLATMOQDA?

Hozirgi kunda ilg'or DevOps, DevSecOps va Cloud muhandislari Vault bilan qanday integratsiyalar qilmoqda?

### 1. Kubernetes: Vault Agent Sidecar Injector
Kubernetes klasterida mikroservis `.env` fayl ishlatmaydi:
* Pod manifestiga maxsus annotatsiya qo'shiladi:
  ```yaml
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "payment-role"
    vault.hashicorp.com/agent-inject-secret-config: "secret/data/organizations/sarvartech/payment/prod"
  ```
* Vault Agent avtomatik ravishda Pod ichiga Sidecar bo'lib kiradi, tokenni yangilab turadi va secretni xotiradagi virtual faylga (`/vault/secrets/config`) yozadi. Ilova esa faylni o'qiydi.

### 2. CI/CD Pipeline (GitLab CI / GitHub Actions) OIDC Bilan
* CI/CD runnerlarida qattiq token saqlanmaydi!
* GitLab yoki GitHub Actions Vault bilan **OIDC / JWT** orqali bog'lanadi.
* Har bir CI/CD build boshlanganda Vault build tokenini tekshirib, unga 10 daqiqalik vaqtinchalik ruxsat beradi. Build tugagach, huquq darhol o'chadi.

### 3. Terraform (Infrastructure as Code)
* Yangi serverlar, ma'lumotlar bazalari va tarmoqlarni ko'tarishda Terraform parollarni qo'lda yozmaydi:
  ```hcl
  data "vault_generic_secret" "db_password" {
    path = "secret/organizations/sarvartech/db"
  }
  ```

### 4. 6 Tilda Tayyor SDK Orqali Integratsiya
Dasturchilar to'g'ridan-to'g'ri kutubxonalar orqali bog'lanadi:
* **Python:** `hvac` kutubxonasi
* **Node.js:** `axios` yoki `@hashicorp/vault`
* **Go:** `github.com/hashicorp/vault/api`
* **PHP / Java / C#:** REST API va native mijozlar.

---

## 7. SARVARTECH INFRATUZILMASI ASBOBLARI

Ushbu repozitoriyda murakkab CLI buyruqlarini eslab qolish shart bo'lmagan maxsus ishlab chiqarilgan avtomatlashtirish tizimlari mavjud:

### 1. `vault-panel` (Interactive CLI Console)
* Fayl: [`vault_panel.py`](file:///c:/Users/user/Documents/vault-srv/vault_panel.py)
* Terminalda `vault-panel` buyrug'i orqali ishga tushadi.
* **Xususiyatlari:**
  * 🏢 Multi-tenant tashkilotlar va servislar qo'shish vizardi.
  * 🎲 24 belgili kriptografik parol generatori.
  * 🎟️ 1-klikda Source IP ga bog'langan xavfsiz token yaratish.
  * 📜 Real-time Audit & IP tahlili oqimi.
  * 💾 1-klikda shifrlangan Raft Snapshot Backup & Restore.
  * 🩺 **Production Doctor:** Tizim xotirasi, `mlock`, disk, portlar va muhr holatini 1 soniyada diagnostika qilish.

### 2. Web Management Console
* Fayllar: [`web_server.py`](file:///c:/Users/user/Documents/vault-srv/web_server.py) & [`web/`](file:///c:/Users/user/Documents/vault-srv/web/)
* Manzil: `https://vault-srv.sarvartech.uz/app/`
* **Xususiyatlari:**
  * **🔍 Spotlight Command Palette (`Ctrl+K`):** Istalgan joydan turib bir necha millisekundda qidiruv.
  * **🧪 Live Test Request:** Secret yoki tokenni yaratgach, dasturchiga berishdan oldin Vaultga real HTTP so'rov yuborib javob kodi (`200 OK`) va kechikishni (`16 ms`) tekshirib olish.
  * **📍 Avtomatik Source IP Aniqlash:** Administrator turgan tarmoq IP manzilini bir tugma bilan aniqlash.
  * **📋 6 Tilda Tayyor Kod Generator:** Dasturchi uchun `.env`, cURL, Python, Node.js, Go va PHP integratsiya kodlarini tayyorlab berish.

---

## 8. ADMINISTRATORNING 5 TA QAT'IY TAQIQLANGAN XATOSI

1. ❌ **Root Tokenni tarqatish:** Initial Root Token faqat birinchi o'rnatish uchun mo'ljallangan. Barcha sozlashlar tugagach, u bekor (revoke) qilinishi shart!
2. ❌ **Unseal kalitlarini serverda qoldirish:** Unseal kalitlarini `/root/keys.txt` da saqlash — uyingiz kalitini eshik tutqichiga ilib qo'yish bilan barobar.
3. ❌ **Audit Devices yoqmaslik:** Audit logi bo'lmagan Vault server ko'r odamga o'xshaydi.
4. ❌ **Siyosatda `path "secret/*"` va `capabilities = ["*"]` berish:** Bu Zero-Trust falsafasini butunlay yo'qqa chiqaradi.
5. ❌ **Zaxira nusxalarini tiklab ko'rmaslik:** Qayta tiklanishi sinab ko'rilmagan zaxira — bu mavjud bo'lmagan zaxiradir.

---

## 9. XULOSA

HashiCorp Vault — zamonaviy xavfsizlikning asosi hisoblanadi. Uni to'g'ri arxitektura va avtomatizatsiyalar bilan sozlash orqali har qanday tashkilot kiberxavfsizlik darajasini eng yuqori bank standartlariga olib chiqishi mumkin.

Ushbu repozitoriy va workshop dasturi sizga nazariy bilimlarni emas, balki real ishlab chiqarishda sinalgan amaliy yechimlarni taqdim etadi.

* **GitHub:** [https://github.com/sarvartech/vault-srv](https://github.com/sarvartech/vault-srv)
* **Prezentatsiya:** [WORKSHOP_SLIDES.html](file:///c:/Users/user/Documents/vault-srv/WORKSHOP_SLIDES.html)
* **O'quv Dasturi:** [WORKSHOP_REJA.md](file:///c:/Users/user/Documents/vault-srv/WORKSHOP_REJA.md)
* **Muallif:** SarvarTech Security & DevOps Team
