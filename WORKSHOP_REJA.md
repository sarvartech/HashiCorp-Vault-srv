# 🛡️ ZERO TO MASTERING VAULT: PRODUCTION ADMINISTRATOR WORKSHOP
### "0 dan Mastering Vaultgacha" — 7 Kunlik Keng Qamrovli Amaliy Dastur (Jami: 14 Soat)
**Muallif:** Vault Production Administrator & DevSecOps Muhandisi  
**Format:** Har kuni 2 soat (YouTube Live Stream + Oflayn Talabalar Guruhi)  
**Tizim bazasi:** `vault-srv.sarvartech.uz` (Ubuntu / Debian / RHEL / Rocky Linux)

---

## 🎯 KURS FALSAFASI VA DARAJALANISH
Ushbu 14 soatlik workshop talabani **mutlaq 0 (boshlang'ich)** darajadan qabul qilib, bosqichma-bosqich **Enterprise darajadagi Mustaqil Vault Administratori (Master)** darajasiga olib chiqadi:

```text
[BOSQICH 1: 0 DARAJA]    --> [BOSQICH 2: AMALIYOTCHI] --> [BOSQICH 3: DEVSECOPS]      --> [BOSQICH 4: MASTER ADMIN]
- Parollar muammosi           - KV v1 / v2 Engine          - AppRole & CI/CD               - Raft HA Klaster (Quorum)
- Kriptografiya & AES         - Multi-tenant Tree          - Dinamik Baza (PostgreSQL)     - Disaster Recovery (Raft Snap)
- Vault qanday ishlaydi       - Tokenlar & Accessor        - PKI (Avto SSL sertifikat)     - Forensika & Fail-Closed Audit
- O'rnatish & Shamir Unseal   - Granular ACL Policies      - Transit Engine (EaaS)         - Maxsus Boshqaruv Skriptlari
```

---

## ⏱️ KUNLIK 2 SOATLIK EFIRNING ANIQ TAQSIMOTI
* **00:00 – 00:25 (25 daqiqa):** 🧠 **Nazariya, Ichki Mexanizmlar & Algoritmlar** (Kriptografiya, xotira, konsensus, arxitektura).
* **00:25 – 01:25 (60 daqiqa):** 💻 **Jonli Amaliyot (Hands-on Terminal & Code)**: CLI buyruqlar bazasi, REST API, Web UI, SDK lar.
* **01:25 – 01:45 (20 daqiqa):** 💥 **Troubleshooting & Avariya Laboratoriyasi**: Serverni ataylab buzish, xatolarni tahlil qilish va tiklash.
* **01:45 – 02:00 (15 daqiqa):** ❓ **Savol-Javob (Q&A) & Oflayn Talabalar Kodini Tekshirish**: Ochiq muloqot va uy vazifasi tahlili.

---

## 📅 7 KUNLIK TO'LIQ VA KENG QAMROVLI DASTUR

---

### 📌 1-KUN: [NOL DARAJA] Kirish, Kriptografiya Asoslari, Vault Core & O'rnatish
**Maqsad: "0" dan boshlab xavfsizlik tushunchasini shakllantirish va birinchi xavfsiz Vault serverni ko'tarish.**

1. **Nazariy qism (25 daqiqa):**
   - Nega `.env`, `config.json` yoki hardcoded parollar xavfli? *Secret Sprawl* nima?
   - Kriptografiya asoslari: Simmetrik (AES-256) vs Asimmetrik (RSA/ECC) shifrlash, Xeshirlash (SHA-256) vs Shifrlash.
   - **Vault Arxitekturasi:** HTTP API, Encryption Barrier, Barrier Cache, Storage Backend (Raft vs File vs Consul).
   - **Memory Locking (`mlock`):** Nega RAM dagi parollar Linux SWAP diskiga tushib qolishi taqiqlangan?
   - **Shamir's Secret Sharing:** Matematik formula, $N$ ta kalit ulushi (Shares) va $T$ ta minimal chegara (Threshold).
   - Vault holatlari (Lifecycle): *Uninitialized ➔ Sealed ➔ Unsealed ➔ Active/Standby*.

2. **Jonli Amaliyot (60 daqiqa):**
   - Linux (Ubuntu/Debian va RHEL/Rocky Linux) serverda Vaultni to'g'ri o'rnatish (`setup_vault_production.py` misolida).
   - Konfiguratsiya fayli (`/etc/vault.d/vault.hcl`): Storage Raft, TCP Listener, UI yoqish.
   - `systemd` xizmatini sozlash (`vault.service`), xavfsiz user (`vault:vault`) va `cap_ipc_lock` berish.
   - Initsializatsiya: `vault operator init -key-shares=5 -key-threshold=3`.
   - Muhrni ochish (`vault operator unseal`) va server holatini tekshirish (`vault status`).
   - Nginx Reverse Proxy sozlash va HTTPS (SSL/TLS) terminatsiyasi (`https://vault-srv.sarvartech.uz`).

3. **Troubleshooting & Avariya Laboratoriyasi (20 daqiqa):**
   - `mlock: cannot allocate memory` xatosi va uni `/etc/security/limits.d/` orqali to'g'rilash.
   - Server o'chib yonganda (reboot) ishlab chiqarish to'xtamasligi uchun `vault-auto-unseal.service` ni sozlash.

4. **Q&A va Oflayn amaliyot (15 daqiqa):**
   - Oflayn talabalar o'z noutbuklarida / VMlarida serverni ko'tarib, `vault status` tekshiruvidan o'tadi.

---

### 📌 2-KUN: [AMALIYOTCHI] Vault Daraxti (Tree), KV Secrets Engine (v1 vs v2) & REST API
**Maqsad: Ma'lumotlarni qat'iy enterprise iyerarxiyada tashkil qilish, versiyalash va to'liq CRUD amallari.**

1. **Nazariy qism (25 daqiqa):**
   - Secrets Engines nima? Vault URL yo'llarni drayverlarga qanday tarqatadi (`sys/`, `auth/`, `secret/`)?
   - **KV v1 va KV v2 chuqur taqqoslash:** Versiyalash mexanizmi qanday ishlaydi?
   - Check-and-Set (CAS) nima va poygalardan (Race conditions) qanday himoyalaydi?
   - Soft Delete (`delete`), Undelete (`undelete`) va Hard Destroy (`destroy`) farqlari.
   - **Enterprise Daraxt Modeli (Production Tree):**
     ```text
     secret/data/organizations/{bank_branch}/{microservice}/{prod|stage|dev}
     ```

2. **Jonli Amaliyot (60 daqiqa):**
   - KV v2 engine yoqish: `vault secrets enable -path=secret kv-v2`.
   - Buyruqlar bazasi (Command-Base): `vault kv put`, `get`, `patch` (mavjud kalitlarni buzmasdan yangilash).
   - Versiyalarni boshqarish: `vault kv get -version=1`, `vault kv delete -versions=2`, `vault kv undelete`.
   - Metadata bilan ishlash: `max-versions=10`, `delete-version-after=30d`.
   - **cURL va REST API:** Dasturchi Vault bilan qanday gaplashadi?
     ```bash
     curl -H "X-Vault-Token: $TOKEN" https://vault-srv.sarvartech.uz/v1/secret/data/...
     ```
   - JSON payload formatlash, `jq` bilan tahlil qilish va Web UI orqali ko'rish.

3. **Troubleshooting & Avariya Laboratoriyasi (20 daqiqa):**
   - Tasodifan butun tashkilot secretlari o'chirib yuborilganda metadata orqali qaytarish.
   - `cas_required=true` bo'lganda bir vaqtning o'zida ikkita administrator yozishga uringanda yuzaga keladigan xatoni yechish.

4. **Q&A va Oflayn amaliyot (15 daqiqa):**
   - Oflayn talabalar 3 ta real bank mikroservisi uchun daraxt strukturasini yaratadi.

---

### 📌 3-KUN: [AMALIYOTCHI] Autentifikatsiya, Tokenlar Anatomiyasi va Accessor Mexanizmi
**Maqsad: Identifikatsiyani to'g'ri o'rnatish, vaqtinchalik kalitlar (TTL) va xavfsiz boshqaruv.**

1. **Nazariy qism (25 daqiqa):**
   - Authentication (Autentifikatsiya) vs Authorization (Ruxsat).
   - **Tokenlar Turlari:** Service Token, Batch Token, Orphan Token, Periodic Token.
   - **Lease va TTL mexanizmi:** `lease_duration`, `renewable`, `ttl`, `max_ttl`, `explicit_max_ttl`.
   - **Token Accessor siri:** Nega xavfsizlik mutaxassisi tokenni bilishi shart emas va faqat Accessor orqali boshqarishi kerak?
   - Root Token xavfi: Nega birlamchi sozlashdan so'ng Root tokenni bekor qilish (`vault token revoke`) shart?

2. **Jonli Amaliyot (60 daqiqa):**
   - Cheklangan token yaratish: `vault token create -ttl=2h -use-limit=1 -orphan -policy=...`.
   - Tokenni uzaytirish (`vault token renew`) va tekshirish (`vault token lookup`).
   - Token Accessor orqali tokenni qidirish va darhol bekor qilish (`vault token revoke -accessor ...`).
   - **Userpass Auth Engine:** Xodimlar va administratorlar uchun login/parol yaratish.
   - Token Role yaratish (Dasturchilarga faqat 2 soatlik cheklangan tokenlar beruvchi shablonlar).

3. **Troubleshooting & Avariya Laboratoriyasi (20 daqiqa):**
   - "Lease Expired" xatosi: Ilova ishlab turib birdan parolsiz qolganda nima qilish kerak?
   - Token Sprawl (Xotirada 100,000 ta bekor qilinmagan token to'planib qolganda tozalash).

4. **Q&A va Oflayn amaliyot (15 daqiqa):**
   - Talabalar bir-biriga 1-martalik (`num_uses=1`) va muddatli tokenlar tarqatib test qiladi.

---

### 📌 4-KUN: [DEVSECOPS] Granular ACL Policies va Zero-Trust Hardening
**Maqsad: "Least Privilege" printsipiga muvofiq bank darajasidagi xavfsizlik siyosatlarini yozish.**

1. **Nazariy qism (25 daqiqa):**
   - Default Deny falsafasi (Ruxsat berilmagan hamma narsa taqiqlangan).
   - Capabilities matritsasi: `create`, `read`, `update`, `delete`, `list`, `sudo`, `deny`.
   - Yo'llarni to'g'ri ko'rsatish: `+` (bitta segment) vs `*` (rekursiv barcha yo'llar).
   - Nozik nuqta: `secret/data/*` vs `secret/metadata/*` farqlari.
   - Dinamik Templating: `identity.entity.aliases.*.name` orqali har bir foydalanuvchiga faqat o'z papkasini ajratish.

2. **Jonli Amaliyot (60 daqiqa):**
   - Enterprise Policy yozish:
     * `developer-read-only.hcl`
     * `ci-cd-billing-service.hcl`
     * `super-admin-policy.hcl`
   - Siyosatni yuklash va sinash: `vault policy write`, `vault token capabilities`.
   - Boshqa tashkilotning papkasini ko'rishni butunlay to'sib qo'yish (`deny` qoidasi).
   - IP Manzil bo'yicha cheklov: `bound_cidrs` siyosatini kiritish.

3. **Troubleshooting & Avariya Laboratoriyasi (20 daqiqa):**
   - "Permission Denied" xatosini qadamma-qadam audit log va `token capabilities` orqali tahlil qilish.
   - Politsiyadagi xavfli "teshiklar" (wildcard `*` suiiste'mol qilinishi) ni aniqlash.

4. **Q&A va Oflayn amaliyot (15 daqiqa):**
   - Talabalarga "buzilgan" siyosat beriladi, uni to'g'irlash topshirig'i bajariladi.

---

### 📌 5-KUN: [DEVSECOPS] Mikroservislar, AppRole, Dinamik Parollar & NAT
**Maqsad: Inson omilisiz xavfsizlik: Backend servislar, CI/CD, Dinamik Database kalitlari va NAT tarmoqlari.**

1. **Nazariy qism (25 daqiqa):**
   - Server-to-Server xavfsizligi: Nega har qanday ilova parolini kodda qoldirish jinoyat?
   - **AppRole mexanizmi:** `role_id` (Username o'rnida) va `secret_id` (Parol o'rnida).
   - **Response Wrapping (Cubbyhole):** `secret_id` ni 120 soniyalik shifrlangan qutida uzatish.
   - **Dinamik Database Secrets Engine:** Baza parollari statik saqlanmaydi! Vault har bir so'rov uchun 1 soatlik yangi user ochib, vaqti o'tgach avtomatik o'chiradi.
   - **Bank NAT va Dinamik Tarmoqlar Muammosi:**
     * Nega `bound_cidrs` adashadi? Nginx `real_ip` moduli va `X-Forwarded-For` zanjiri qanday ishlaydi?

2. **Jonli Amaliyot (60 daqiqa):**
   - AppRole yoqish va to'liq sozlash (`secret_id_ttl=24h`, `token_ttl=1h`).
   - Python (`hvac`), Node.js (`axios`), Go va cURL yordamida AppRole login amaliyoti.
   - Dinamik PostgreSQL/MySQL Secret Engine yoqish va 1 soatlik vaqtinchalik login/parol generatsiyasini sinash.
   - NAT muhitida to'g'ri `bound_cidrs` va subnet maskalarini (`192.168.0.0/16`) belgilash.

3. **Troubleshooting & Avariya Laboratoriyasi (20 daqiqa):**
   - `Secret-ID expired` va `Wrapping token already revoked` xatolarini yechish.
   - Mikroservis ichida tokenni avtomatik yangilab turuvchi (background renewer loop) kod yozish.

4. **Q&A va Oflayn amaliyot (15 daqiqa):**
   - Talabalar o'z kompyuteridagi scriptni serverdagi AppRole ga ulab secretlarni oladi.

---

### 📌 6-KUN: [MASTER ADMIN] PKI (X.509 SSL), Transit Engine (EaaS) & Audit Forensika
**Maqsad: Dinamik SSL sertifikatlar tarqatish, ma'lumotlarni shifrlash xizmati va bank darajasidagi audit.**

1. **Nazariy qism (25 daqiqa):**
   - **PKI Secrets Engine:** Korporativ CA (Certificate Authority) bo'lish. Nega qo'lda SSL sertifikat o'rnatish o'tmishda qoldi?
   - **Transit Secrets Engine (Encryption as a Service):** Ma'lumotlarni Vaultda saqlamasdan, shunchaki shifrlab (`encrypt`) yoki yechib (`decrypt`) berish.
   - **Audit Device va Fail-Closed tamoyili:** Agar audit log yozilmasa, Vault nima qiladi? (Butun server to'xtaydi!).
   - **HMAC-SHA256 xeshirlash:** Nega audit logda maxfiy kalitlar ochiq holda ko'rinmaydi?

2. **Jonli Amaliyot (60 daqiqa):**
   - PKI Engine orqali 30 kunlik ichki TLS/SSL sertifikatlar generatsiya qilish (`vault write pki/issue/...`).
   - Transit Engine orqali foydalanuvchi pasport ma'lumotlari yoki kredit karta raqamlarini shifrlash (`vault write transit/encrypt/...`).
   - Fayl audit qurilmasini yoqish: `/var/log/vault/vault_audit.log`.
   - `tail -f` va `jq` yordamida jonli ravishda so'rovlar oqimini kuzatish.
   - `vault audit-hash` buyrug'i bilan xeshni solishtirish.

3. **Troubleshooting & Avariya Laboratoriyasi (20 daqiqa):**
   - Audit fayli to'lib qolganda yoki huquqlar buzilganda muzlab qolgan Vaultni tezkor qutqarish.
   - Audit log rotatsiyasi (`logrotate`) va Dual-audit (File + Syslog).

4. **Q&A va Oflayn amaliyot (15 daqiqa):**
   - Talabalar bir-birining audit logidan shubhali kirishlarni qidirib topadi.

---

### 📌 7-KUN: [MASTER ADMIN] Raft HA Klaster, Falokatdan Tiklash (DR), Boshqaruv Skriptlari & Yakun
**Maqsad: Yuqori bardoshli klaster (HA), 1-klikda zaxiralash va Vault Administratorlik sertifikati.**

1. **Nazariy qism (25 daqiqa):**
   - **Integrated Raft HA Klaster:** Leader, Follower, Quorum ($N/2 + 1$), Heartbeat va Saylov mexanizmi.
   - Split-Brain xavfi va `peers.json` orqali favqulodda tiklash.
   - CIS Benchmark va Bank Hardening Checklist.
   - `vault-srv` dagi maxsus asboblar: `vault_panel.py` (CLI) va `web_server.py` arxitekturasi tahlili.

2. **Jonli Amaliyot (60 daqiqa):**
   - Raft Snapshot olish: `vault operator raft snapshot save /backups/vault_backup.snap`.
   - Serverni ataylab "yo'q qilish" (barcha ma'lumotlarni o'chirib tashlash).
   - Snapshotdan qayta tiklash: `vault operator raft snapshot restore -force ...`.
   - `vault_panel.py` dagi **Production Doctor** modulini yurgizib tizim sog'lig'ini tekshirish.
   - Web Konsoldagi Spotlight (`Ctrl+K`), Live Test Request va 6 tildagi kod generatorlarini sinash.

3. **Troubleshooting & Avariya Laboratoriyasi (20 daqiqa):**
   - Unseal kalitlari bitta adminning qo'lida qolib ketganda nima bo'ladi?
   - Quorum yo'qotilganda klaster qanday jonlantiriladi?

4. **Katta Q&A, Yakuniy Imtihon va Sertifikatlash (15 daqiqa):**
   - Efir tomoshabinlari va oflayn talabalar bilan ochiq muloqot, sertifikatlash va masterclass yakuni!

---

## 🏆 KURS YAKUNIDA TALABA NIMALARGA QODIR BO'LADI?
1. Noldan boshlab har qanday Linux serverda bank xavfsizlik talablariga mos HashiCorp Vault klasterini o'rnatish.
2. Har qanday mikroservis, CI/CD va dasturchilar uchun to'g'ri Zero-Trust ruxsatnomalarini berish.
3. Klaster halokatga uchraganda bir necha daqiqada zaxiradan to'liq qayta tiklash.
4. Xavfsizlik bo'yicha audit jurnallarini o'qish va kiberhujumlarni aniqlash.
5. Maxsus CLI (`vault-panel`) va Web panellarni o'zi mustaqil ishlab chiqish va integratsiya qilish.

---

## 💻 LABORATORIYA (LAB) INFRATUZILMASI VA TALABLARI

### 🏢 1. Bizning Asosiy Master Muhitimiz (Efir va Dars uchun):
* **Gipervizor:** Ofis/studiyamizdagi jismoniy **Proxmox VE Server**.
* **Virtual Mashinalar (VM):**
  * **OS:** Ubuntu 22.04 / 24.04 LTS yoki Rocky Linux 9 (x64)
  * **Resurs:** 2 vCPU, 2-4 GB RAM, 20 GB NVMe/SSD
  * **Tarmoq:** Bridged / NAT (Static LAN IP) + Barqaror Internet aloqasi
  * **Domen:** `https://vault-srv.sarvartech.uz` (Nginx Reverse Proxy & SSL)

### 👥 2. Talabalar va Tomoshabinlar Uchun Tavsiya:
* **Majburiy qolip yo'q!** Har bir talaba o'ziga eng qulay va qo'lida bor bo'lgan muhitni tanlaydi va bizning efirga qarab bir xil buyruqlarni o'zida parallel bajaraveradi:
  * 🖥️ **Variant A (Noutbukda bepul):** VirtualBox, VMware Workstation yoki Ubuntu Multipass / WSL2.
  * 🏢 **Variant B (Mahalliy serverda):** O'zlarining Proxmox VE, ESXi yoki KVM gipervizorlari.
  * ☁️ **Variant C (Bulutda - Cloud VPS):** Hetzner, Selectel, DigitalOcean, AWS yoki istalgan $4-5 lik Linux VPS.
* **Talaba uchun minimal talablar:**
  1. Istalgan Linux VM (Ubuntu yoki Rocky Linux).
  2. SSH orqali terminalga kirish imkoni (PuTTY, MobaXterm, VS Code yoki Windows Terminal).
  3. Barqaror internet (paketlarni yuklab olish uchun).
