# 📑 ZERO TO MASTERING VAULT: PRODUCTION ADMINISTRATOR WORKSHOP
## "0 dan Mastering Vaultgacha" — Slaydlar Matni, Arxitektura Chizmalari va Spiker Eslatmalari (PPT Slide Deck)
*PowerPoint, Google Slides, Keynote yoki Marp orqali taqdimot qilish uchun to'liq tayyorlangan.*

---

<!-- SLIDE 1 -->
# [SLAYD 1] Muqova (Title Slide)
- **Katta Sarlavha:** ZERO TO MASTERING VAULT
- **Kichik Sarlavha:** 0 dan Bank Darajasidagi HashiCorp Vault Administratorligigacha
- **Format:** 7 Kunlik Intensiv Amaliy Workshop (Jami: 14 Soat)
- **Tizim bazasi:** `vault-srv.sarvartech.uz` (Ubuntu / Debian / RHEL / Rocky Linux)
- **Spiker:** Vault Production Administrator & DevSecOps Muhandisi
- **Spiker Eslatmasi (Speaker Note):**
  > *"Assalomu alaykum do'stlar va qadrli talabalar! Bugun biz nol darajadan boshlab, zamonaviy bank va enterprise infratuzilmasining eng muhim xavfsizlik asosi — HashiCorp Vaultni 'Mastering' darajasigacha o'rganadigan 14 soatlik to'liq amaliy workshopimizni boshlaymiz. Bu yerda siz shunchaki buyruqlarni yodlamaysiz — ichki shifrlash to'sig'i, xotira blokirovkasi, Raft kvorumi, dinamik parollar, PKI sertifikatlari va zaxiradan qayta tiklashgacha bo'lgan barcha sirlarni o'z qo'lingiz bilan bajarasiz!"*

---

<!-- SLIDE 2 -->
# [SLAYD 2] 4 Ta Bosqich: Noldan Master Darajasigacha
```text
  [BOSQICH 1: 0 DARAJA]    --> [BOSQICH 2: AMALIYOTCHI] --> [BOSQICH 3: DEVSECOPS]      --> [BOSQICH 4: MASTER ADMIN]
  - Parollar muammosi           - KV v1 / v2 Engine          - AppRole & CI/CD               - Raft HA Klaster (Quorum)
  - Kriptografiya & AES         - Multi-tenant Tree          - Dinamik Baza (PostgreSQL)     - Disaster Recovery (Raft Snap)
  - Vault qanday ishlaydi       - Tokenlar & Accessor        - PKI (Avto SSL sertifikat)     - Forensika & Fail-Closed Audit
  - O'rnatish & Shamir Unseal   - Granular ACL Policies      - Transit Engine (EaaS)         - Maxsus Boshqaruv Skriptlari
```
- **Vaqt taqsimoti:** Har kuni 120 daqiqa (25 min Nazariya/Mexanizm + 60 min Hands-on Kod/CLI + 20 min Avariya/Troubleshooting + 15 min Q&A).

---

<!-- SLIDE 3 -->
# [SLAYD 3] [0-DARAJA] Nega Vault? "Secret Sprawl" Falokati
- **Klassik xatoliklar (90% kompaniyalar yo'l qo'yadigan xavf):**
  - Parollar va API kalitlar `.env` yoki config fayllarda ochiq matnda saqlanadi.
  - Git repository'ga bazaning master parollari tushib qoladi (GitHub Secrets Leak).
  - Parol o'zgarsa — 20 ta mikroservisni qayta yurgizish (redeploy) kerak bo'ladi.
  - Dasturchi ishdan ketganda qaysi parollarni bilishini hech kim aniq bilmaydi!
- **Zero-Trust Falsafasi:**
  - *"Hech kimga ishonma, har bir kirishni tekshir va har bir kalitga muddat (TTL) ber!"*
  - Vault barcha maxfiy ma'lumotlarni yagona shifrlangan qutiga jamlaydi va har bir murojaatni qattiq nazorat qiladi.

---

<!-- SLIDE 4 -->
# [SLAYD 4] [0-DARAJA] Kriptografiya Asoslari va Shifrlash To'sig'i
- **Kriptografiya tushunchalari:**
  - **Simmetrik shifrlash (AES-GCM-256):** Bitta kalit bilan shifrlanadi va yechiladi. Vault barcha disk ma'lumotlarini AES-256 bilan shifrlaydi.
  - **Asimmetrik shifrlash (RSA/ECC):** Ochiq va yopiq kalitlar juftligi (PKI va TLS sertifikatlar uchun).
  - **Xeshirlash (SHA-256):** Bir tomonlama qaytmas aylantirish (Audit logdagi parollarni yashirish uchun).
- **Encryption Barrier (Shifrlash To'sig'i):**
  - Storage Backend (Disk) da barcha ma'lumotlar shifrlangan payload ko'rinishida yotadi.
  - Disk o'g'irlansa ham — Master Key'siz ma'lumotni o'qib bo'lmaydi.
- **Memory Locking (`mlock` mexanizmi):**
  - Linux OS xotira to'lganda RAM ma'lumotlarini diskdagi SWAP faylga chiqaradi.
  - `mlock` Vault xotirasidagi parollarni SWAP ga yozilishini jismonan to'sadi.

---

<!-- SLIDE 5 -->
# [SLAYD 5] [0-DARAJA] Shamir's Secret Sharing va Vault Holatlari
- **Matematik taqsimot printsipi:**
  - Master Key yagona shaxs qo'lida saqlanmaydi.
  - U $N$ ta kalit bo'lagiga bo'linadi (**Key Shares = 5**).
  - Uni qayta tiklash uchun minimal kalitlar soni belgilanadi (**Threshold = 3**).
- **Vault Holatlari (Lifecycle):**
  1. **Uninitialized:** Yangi server, kalitlar hali yaratilmagan.
  2. **Sealed (Muhrlangan):** Server ishlayapti, lekin xotiradagi shifr kaliti o'chirilgan, hech kimga javob bermaydi.
  3. **Unsealed (Ochiq):** 3 ta kalit kiritildi, shifrlash to'sig'i ochildi, so'rovlar qabul qilinmoqda.
  4. **Active vs Standby:** HA klasterda Master (Leader) yoki kvorumni saqlovchi Follower.

---

<!-- SLIDE 6 -->
# [SLAYD 6] [1-KUN LAB] O'rnatish, Init va Nginx TLS
- **Konfiguratsiya fayli (`/etc/vault.d/vault.hcl`):**
  ```hcl
  storage "raft" {
    path    = "/opt/vault/data"
    node_id = "vault-node-1"
  }
  listener "tcp" {
    address     = "127.0.0.1:8200"
    tls_disable = 1 # Nginx reverse proxy orqali HTTPS qilinadi
  }
  ui = true
  disable_mlock = false
  ```
- **Initsializatsiya (Init):**
  ```bash
  export VAULT_ADDR="http://127.0.0.1:8200"
  vault operator init -key-shares=5 -key-threshold=3
  ```
- **Auto-Unseal xizmati (`vault-auto-unseal.service`):**
  - Server qayta yuklanganda (reboot) ishlab chiqarish to'xtab qolmasligi uchun avtomatlashtirilgan xavfsiz unseal xizmati.

---

<!-- SLIDE 7 -->
# [SLAYD 7] [AMALIYOTCHI] Production Tree va KV v1 vs v2
- **Enterprise Daraxt Strukturasi (Multi-tenant):**
  ```text
  secret/
  └── data/
      └── organizations/
          ├── sarvartech/
          │   ├── payment-service/
          │   │   ├── prod  --> { db_host, db_pass, api_token }
          │   │   └── stage
          │   └── mobile-app/
          │       └── prod
          └── agrobank/
              └── core-billing/
                  └── prod
  ```
- **KV v1 vs KV v2:**
  - **KV v1:** Versiyalash yo'q, o'chirilsa tiklanmaydi, race condition himoyasi yo'q.
  - **KV v2 (Production):** Avtomatik versiyalash (v1, v2...), Soft Delete (`delete`), Qayta tiklash (`undelete`), Butunlay yo'q qilish (`destroy`), Check-And-Set (CAS).

---

<!-- SLIDE 8 -->
# [SLAYD 8] [2-KUN LAB] KV v2 Command-Base & REST API
- **CLI Buyruqlari:**
  ```bash
  # Yozish (Put)
  vault kv put secret/organizations/sarvartech/billing/prod db_pass="SuperSecret@2026"

  # Qisman yangilash (Patch)
  vault kv patch secret/organizations/sarvartech/billing/prod api_key="sk_live_9921"

  # Versiyalar bo'yicha o'qish
  vault kv get -version=1 secret/organizations/sarvartech/billing/prod

  # Soft-delete va Tiklash
  vault kv delete -versions=2 secret/organizations/sarvartech/billing/prod
  vault kv undelete -versions=2 secret/organizations/sarvartech/billing/prod
  ```
- **cURL va REST API:**
  ```bash
  curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/secret/data/organizations/sarvartech/billing/prod
  ```

---

<!-- SLIDE 9 -->
# [SLAYD 9] [AMALIYOTCHI] Tokenlar Anatomiyasi, TTL va Accessor
- **Token Turlari:**
  - **Service Token:** Standart token, ota-bola daraxtiga ega.
  - **Orphan Token:** Otasi yo'q token. Agar otasi revoke bo'lsa ham tirik qoladi.
  - **Batch Token:** Xotirada saqlanmaydi (stateless), juda yuqori so'rovlar (RPS) uchun.
- **Lease va TTL cheklovlari:**
  - `ttl=2h` — Token faqat 2 soat ishlaydi.
  - `num_uses=1` — Faqat 1 marta secret o'qiladi va token o'zini o'zi yo'q qiladi!
- **Token Accessor siri:**
  - Tokenning o'zini oshkor qilmasdan turib uni tekshirish va bekor qilish (Revoke):
  ```bash
  vault token lookup -accessor "a6KNiBTnyM..."
  vault token revoke -accessor "a6KNiBTnyM..."
  ```

---

<!-- SLIDE 10 -->
# [SLAYD 10] [DEVSECOPS] Granular ACL Policies va Default Deny
- **Falsafa: Default Deny (Ruxsat berilmagan hamma narsa — taqiqlangan).**
- **Bank-Grade Siyosat namunasi (`payment-policy.hcl`):**
  ```hcl
  path "secret/data/organizations/sarvartech/payment-service/*" {
    capabilities = ["read", "list"]
  }

  path "secret/metadata/organizations/sarvartech/payment-service/*" {
    capabilities = ["list", "read"]
  }

  path "secret/*" {
    capabilities = ["deny"]
  }
  ```
- **Siyosatni yuklash va sinash:**
  ```bash
  vault policy write payment-policy payment-policy.hcl
  vault token capabilities <TOKEN> secret/data/organizations/sarvartech/payment-service/prod
  ```

---

<!-- SLIDE 11 -->
# [SLAYD 11] [DEVSECOPS] AppRole va NAT Tarmoqlaridagi Zero-Trust
```text
   +------------------+                   +------------------+
   |    CI/CD / Admin |                   |   Mikroservis    |
   +------------------+                   +------------------+
            │                                      │
      1. Role-ID beradi                      2. Secret-ID oladi
            \                                      /
             ▼                                    ▼
       +------------------------------------------------+
       |               Vault AppRole Login              |
       |          POST /v1/auth/approle/login           |
       +------------------------------------------------+
                              │
                       3. Client Token
                              ▼
                  +-----------------------+
                  | Faqat o'z secretini   |
                  | o'qiy oladi           |
                  +-----------------------+
```
- **NAT Muammosi:** Router/Firewall orqali o'tganda Vaultga Gateway IP ko'rinadi.
- **Yechim:** Nginx `real_ip` moduli, to'g'ri subnet maskasi (`192.168.0.0/16`) va Response Wrapping (`-wrap-ttl=120s`).

---

<!-- SLIDE 12 -->
# [SLAYD 12] [DEVSECOPS] Dinamik Database Parollari (PostgreSQL / MySQL)
- **Nega statik DB parollari xavfli?**
  - Agar bitta dasturchi parolni bilsa yoki logga tushsa — butun baza xavf ostida.
- **Dinamik Secret Engine mexanizmi:**
  1. Ilova Vaultga murojaat qiladi: *"Menga bazaga ulanish ber"*.
  2. Vault PostgreSQL/MySQL da yangi foydalanuvchi yaratadi: `v-approle-billing-xyz123`.
  3. Unga faqat 1 soatlik umr beradi (`TTL = 1h`).
  4. 1 soat o'tgach — Vault ushbu foydalanuvchini bazadan jismonan o'chiradi (REVOKE & DROP ROLE).
- **Natija:** Baza paroli o'g'irlanishi mumkin emas, chunki u doim yangilanadi!

---

<!-- SLIDE 13 -->
# [SLAYD 13] [MASTER ADMIN] PKI Engine: Dinamik TLS/SSL Sertifikatlari
- **Qo'lda SSL sertifikat o'rnatish muammosi:**
  - Sertifikat muddati (1 yil) tugab, server to'xtab qolishi.
  - Yangilashda xizmatlarning uzilishi.
- **Vault PKI (Certificate Authority) yechimi:**
  - Vault ichki CA (Root CA / Intermediate CA) bo'lib xizmat qiladi.
  - Mikroservis start olganda Vaultdan 30 kunlik o'ziga xos X.509 TLS sertifikat oladi.
  - Har 15 kunda avtomatik yangilab turiladi (Zero-downtime mTLS).
  ```bash
  vault write pki/issue/internal-services common_name="billing.sarvartech.uz" ttl="720h"
  ```

---

<!-- SLIDE 14 -->
# [SLAYD 14] [MASTER ADMIN] Transit Engine (Encryption as a Service - EaaS)
- **Kriptografiya qoidasi: Dasturchi o'zi shifrlash algoritmini yozmasligi shart!**
- **Transit Engine qanday ishlaydi?**
  - Ma'lumot Vaultda **SAQLANMAYDI**.
  - Ilova Vaultga ochiq matn (plaintext) yuboradi (masalan, Pasport seriyasi yoki Karta raqami).
  - Vault uni AES-GCM bilan shifrlab qaytaradi: `vault:v1:8f7e...`.
  - Ilova o'z bazasida faqat shifrlangan satrni saqlaydi.
  - O'qish kerak bo'lganda — Vaultga berib yechtirib oladi (`transit/decrypt`).

---

<!-- SLIDE 15 -->
# [SLAYD 15] [MASTER ADMIN] Audit Logging & Forensika (Fail-Closed)
- **Fail-Closed Qoidasi:**
  - Agar Audit Device (Fayl yoki Syslog) ishlamay qolsa yoki to'lib ketsa — **Vault yangi so'rovlarni qabul qilishni to'xtatadi!**
- **HMAC-SHA256 Xeshirlash:**
  - Barcha maxfiy kalitlar va parollar audit logga tushishidan oldin bir tomonlama shifrlanadi.
- **Jonli monitoring:**
  ```bash
  tail -f /var/log/vault/vault_audit.log | jq '{
    time: .time,
    path: .request.path,
    client_ip: .request.remote_address,
    status: .response.data
  }'
  ```

---

<!-- SLIDE 16 -->
# [SLAYD 16] [MASTER ADMIN] Raft HA Klaster va Disaster Recovery (DR)
- **Integrated Raft Konsensus:**
  - Tugunlar: 3 yoki 5 ta tugun (Quorum = 3 bo'lsa 2 ta, 5 bo'lsa 3 ta).
  - Leader so'rovlarni qabul qiladi, Followerlar kvorum saqlaydi.
- **Raft Snapshot (1-klikda to'liq zaxira):**
  ```bash
  vault operator raft snapshot save /backups/vault_$(date +%F).snap
  ```
- **Avariyadan keyin tiklash:**
  ```bash
  vault operator raft snapshot restore -force /backups/vault_backup.snap
  ```
- **Quorum yo'qotilganda favqulodda tiklash:** `/opt/vault/data/raft/peers.json`.

---

<!-- SLIDE 17 -->
# [SLAYD 17] `vault-srv` Boshqaruv Vositalari: `vault-panel.py` va Web Konsol
- **`vault-panel` CLI (1530 qator Python):**
  - Zero-Command boshqaruv: Tashkilotlar, Servislar, Kriptografik parol generatori, IP bog'lash, Zaxira tiklash.
- **Web Management Console (`web_server.py`):**
  - **🔍 Spotlight Command Palette (`Ctrl+K`):** Bir millisekundda qidiruv.
  - **🧪 Live Test Request:** Dasturchiga berishdan oldin Vaultga so'rov yuborib, HTTP status (`200 OK`) va kechikishni (`16 ms`) tekshirish.
  - **💻 6 Tilda Tayyor SDK Generator:** `.env`, cURL, Python (`hvac`), Node.js (`axios`), Go, PHP (`curl`).

---

<!-- SLIDE 18 -->
# [SLAYD 18] Administratorning 5 Ta Qat'iy Taqiqlangan Xatosi!
1. ❌ **Root tokenni dasturchilarga berish yoki `.env` fayllarga yozish.**
2. ❌ **Unseal kalitlarini serverning o'zida `/root/keys.txt` da qoldirish.**
3. ❌ **Audit log qurilmasini yoqmasdan Production serverni ishga tushirish.**
4. ❌ **Hamma narsaga `capabilities = ["*"]` yoki `path "secret/*"` berish.**
5. ❌ **Zaxira nusxalarini (Snapshot) qayta tiklashni hech qachon sinab ko'rmaslik.**

---

<!-- SLIDE 19 -->
# [SLAYD 19] Yakuniy Imtihon, Sertifikatlash va Xulosa
- **Talabalar uchun Master Darajadagi Laboratoriya Imtihoni:**
  1. Noldan Linuxda Vault ko'tarish va Nginx TLS ulash.
  2. Multi-tenant Tree yaratish va AppRole orqali bog'lash.
  3. Avariya simulyatsiyasi: serverni buzish va Snapshotdan 3 daqiqada qayta tiklash.
- **Jonli savol-javob (Q&A).**
- **E'tiboringiz uchun rahmat! 7 kunlik workshop yakunlandi.**
