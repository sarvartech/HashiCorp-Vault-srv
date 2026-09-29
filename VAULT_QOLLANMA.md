# HashiCorp Vault Enterprise - Production Konsol Qo'llanmasi

## 📌 Server Ma'lumotlari
- **Server IP:** `192.168.86.128` (Test server) / `192.168.88.18` (Production)
- **Domen Manzili (URL):** [https://vault-srv.sarvartech.uz](https://vault-srv.sarvartech.uz)
- **Web UI (HTTPS):** [https://vault-srv.sarvartech.uz/ui](https://vault-srv.sarvartech.uz/ui)
- **Root Token:** `<YOUR_VAULT_ROOT_TOKEN>` *(Server initsializatsiya qilinganda beriladi)*
- **Reverse Proxy:** Nginx (Port 443 -> 8200)
- **Audit Log Fayli:** `/var/log/vault/vault_audit.log`
- **Auto-Unseal Holati:** FAOL (`vault-auto-unseal.service`)

---

## 🔄 Domen bilan To'liq Qayta O'rnatish (Re-Install with Domain)

Agar bazani tozalab, noldan domen va reverse proxy bilan qayta o'rnatmoqchi bo'lsangiz:

### 1-usul: Serverning o'zida turib ishga tushirish:
```bash
sudo python3 reinstall_vault.py --domain https://vault-srv.sarvartech.uz -y
```

### 2-usul: Windows kompyuterdan turib masofadan o'rnatish:
```powershell
python deploy_to_any_server.py
```
*(Menyudan `[2] To'liq Qayta Re-install` tanlanadi va server IP, SSH login/parol kiritiladi)*

---

## 🚀 Har Qanday Ishlab Turgan Vault Serverga Ulanish (Universal Login)

Script ishga tushganda avtomatik ravishda **Server URL** va **Root Token** so'raydi:
```bash
vault-panel
```

**Ekranda chiqadigan so'rov:**
```text
============================================================================
   🔐 HASHICORP VAULT CLI-PANEL - TIZIMGA KIRISH (AUTHENTICATION)
============================================================================

🌐 Vault Server URL [https://vault-srv.sarvartech.uz]:  <-- [Enter bosing]
🔑 VAULT ROOT / ADMIN TOKENNI KIRITING:
Tokenni kiriting: <Root tokenni paste qilasiz>

ℹ Token tekshirilmoqda...
✔ Token muvaffaqiyatli qabul qilindi va tasdiqlandi!
  Foydalanuvchi/Display: root | Ruxsatnomalar: root | Status: FAOL
```
*Token Vault serverida tekshiriladi va darhol boshqaruv menyusi ochiladi.*
*Xohlasangiz, boshqa Vault serverining IP manzilini (`http://10.0.0.5:8200` kabi) kiritib, istalgan serverni boshqarishingiz mumkin.*

### 📋 Asosiy Menyu Bo'limlari:

```text
  🏢 TASHKILOTLAR, SERVISLAR VA CREDENTIALS (VIZARD):
  [1]  📂 Tashkilotlar & Servislar tuzilmasi (Production Tree)
  [2]  ➕ Yangi Tashkilot (Organization) qo'shish
  [3]  ⚙️  Yangi Servis qo'shish (Auto-Password & Shablonlar bilan)
  [4]  🔑 Servis Credentials (Password/Token/Key) ko'rish
  [5]  ✏️  Servis Credentials qo'shish, yangilash yoki parol generatsiyasi
  [6]  🗑  Servis yoki Tashkilotni o'chirish
  
  🛡️  RUXSATLAR VA XAVFSIZLIK (SOURCE IP BOG'LASH BILAN):
  [7]  🎟  Yangi Token yaratish (1-klikda Source IP bog'langan)
  [8]  🤖 Mikroservislar uchun AppRole (Role-ID & Secret-ID)
  [9]  👤 Xodim/Operator qo'shish (Userpass Login)
  [10] 🛡  ACL Policy'larni ko'rish va boshqarish

  🚀 PRODUCTION ADMIN VA TIZIM NAZORATI:
  [11] 📜 Real-time Audit & Access Monitor (Kirishlar va IP tahlili)
  [12] 💾 Avtomatlashtirilgan Zaxiralash (1-Click Backup)
  [13] 🔄 Zaxiradan qayta tiklash (1-Click Restore)
  [14] 🩺 Production Doctor (Tizim diagnostikasi)
  [15] 🧱 Firewall (UFW) va Portlarni boshqarish
  [16] 🌐 Web UI Ma'lumotlari (Brauzer orqali kirish)
```

---

## 🌐 Yangilangan Web Management Console (Bank-Grade UI/UX)

Web konsol brauzer orqali serverni qulay boshqarish uchun to'liq ishga tushirilgan:
- **Port orqali kirish:** [http://192.168.86.128:5000](http://192.168.86.128:5000)
- **Domen orqali kirish (HTTPS Reverse Proxy):** [https://vault-srv.sarvartech.uz/app/](https://vault-srv.sarvartech.uz/app/)

### 🌟 Yangi qo'shilgan imkoniyatlar:
1. **🔍 Spotlight Command Palette (`Ctrl+K` yoki `⌘+K`):**
   - Istalgan sahifada `Ctrl+K` tugmasini bosing — bir necha millisekundda tashkilotlar, servislar, tokenlar yoki amallarni qidirib, to'g'ridan-to'g'ri o'ting.
2. **🧪 Jonli Test Qilish (Live Test Request):**
   - Har bir secret va token yaratilganda uni dasturchiga yuborishdan oldin **"Sinash (Test Request)"** tugmasini bosib tekshirib ko'rishingiz mumkin.
   - Tizim real vaqtda Vault serverga so'rov yuborib, HTTP javob kodi (`200 OK`), server kechikishi (`16 ms`) va olingan JSON payloadni ko'rsatadi.
3. **📍 Avtomatik Source IP Aniqlash:**
   - IP manzilni qo'lda kiritish shart emas! Token, AppRole yoki Vizard maydonlarida **"📍 Mening IP'm"** tugmasini bosing — server murojaat qilayotgan kompyuteringiz IP manzilini (`192.168.86.1` kabi) avtomatik aniqlab kiritadi.
4. **💻 6 ta Dasturlash Tilida Tayyor Integratsiya Kodi:**
   - Dasturchiga beriladigan kartada quyidagi formatlarda tayyor kod chiqadi:
     - ⚡ `.env` (Environment variables)
     - 💻 `cURL` (Terminal va jq)
     - 🐍 `Python` (`hvac` va `requests` kutubxonasi)
     - 🟢 `Node.js` (`axios` orqali)
     - 🔵 `Go` (`github.com/hashicorp/vault/api`)
     - 🐘 `PHP / Laravel` (`curl` orqali)
5. **🎲 Interaktiv Kriptografik Parol Generatori:**
   - Yuqori paneldagi `🎲 Generator` tugmasi orqali istalgan uzunlikdagi (12 dan 64 belgili) kriptografik kuchli parollarni bir klikda yaratish va xavfsizlik darajasini (entropiya) nazorat qilish mumkin.
6. **📋 Jadval (Table) va { } Raw JSON Ko'rinishlari:**
   - Secretlarni nafaqat jadval shaklida, balki bevosita JSON formatida tahrirlash, boshqa konfiguratsiyalardan nusxa ko'chirib joylash va avtomatik formatlash (Prettify) mumkin.

---

## 💎 Administrator uchun Qulayliklar (Zero Manual Commands):

1. **Avtomatik Parol va API Key Generatori:**
   - Parol o'ylab topish shart emas — tizim avtomatik 24-belgili kriptografik xavfsiz parollar (`A-Z`, `a-z`, `0-9`, maxsus belgilar) va API tokenlarni generatsiya qiladi.
2. **Erkin Maydonlar (Administrator Custom Key-Value Inputs):**
   - Hech qanday majburiy shablonlar yo'q — administrator o'z servisi uchun kerakli maydonlarni (`username`, `password`, `api_token`, `db_host`, `private_key` va h.k.) erkin shaklda o'zi qo'shadi va to'ldiradi. Har bir maydon uchun ixtiyoriy 24-belgili parol generatori mavjud.
3. **Avtomatik Source IP Aniqlash:**
   - IP manzilni qo'lda terish shart emas — panel ulanib turgan administrator yoki server IP manzilini avtomatik aniqlaydi va bir klik bilan bog'laydi.
4. **Real-time Audit Tizimi:**
   - Kim, qachon, qaysi IP manzildan qaysi secretni o'qiganini to'g'ridan-to'g'ri jadval ko'rinishida ko'rish mumkin.
5. **1-Click Zaxiralash va Tiklash (Backup/Restore):**
   - Barcha tashkilotlar va parollar shifrlangan holatda zaxiralanadi va kerak bo'lganda bir tugma bilan qayta tiklanadi.
6. **Production Doctor:**
   - Vault servisi, Auto-unseal, Firewall, Muhr holati, RAM bandligi, Disk sig'imi va Audit loglari 1 sekundda tekshirilib, status beriladi.

---

## 🏷️ Dasturchiga Beriladigan vs Administrator Ichki Ma'lumotlari:

### 1. Dasturchiga BERILADIGAN Blok (Copy-Paste qilib yuboriladi):
- **Server URL:** `http://192.168.86.128:8200` yoki `https://vault-srv.sarvartech.uz`
- **Client Token:** `hvs.CAESII...` *(faqat o'zining servisiga ruxsatli token)*
- **Xavfsizlik turi:** `1-martalik Bootstrap Token (num_uses=1)` yoki `AppRole (Role ID + Secret ID)`
- **.env fayli uchun:** `VAULT_ADDR=http://192.168.86.128:8200` va `VAULT_TOKEN=hvs.CAES...`
- **Tayyor kod bloki:** Python, Node.js, Go, PHP yoki cURL buyrug'i

### 2. Dasturchiga BERILMAYDIGAN Ichki Ma'lumotlar (Faqat adminda qoladi):
- ❌ **Accessor:** `a6KNiBTnyM...` *(Bu tokenning ichki tizim identifikatori, faqat tokenni bekor qilish yoki audit qilishda kerak)*
- ❌ **Root Token:** `<ROOT_TOKEN>` *(Umuman hech kimga berilmaydi)*
- ❌ **Unseal Kalitlari:** *(Hech qachon berilmaydi)*
- ❌ **Server mahalliy manzili (`127.0.0.1`):** *(Tashqi tarmoqdagi dasturchida ishlamaydi, shuning uchun `192.168.86.128` yoki domen beriladi)*

---

## 🛡️ NAT VA DINAMIK TARMOQLAR UCHUN ZERO-TRUST XAVFSIZLIK MEXANIZMLARI

### ❓ Nega IP orqali cheklash (bound_cidrs) NAT muhitida o'chirildi?
Zamonaviy bank infratuzilmasida ilovalar ko'pincha:
1. **Boshqa tarmoq (VLAN / Subnet)** orqali marshrutizator/firewall orqali o'tadi.
2. **Kubernetes klasteri yoki Docker Swarm** ichidan chiquvchi NAT (SNAT) orqali chiqadi.
3. **Mikroservislar konteynerlari qayta yuklanganda** ularning ichki IP manzillari dinamik ravishda o'zgaradi.

> [!WARNING]
> Agar bunday muhitda qat'iy IP cheklovi qo'yilsa:
> - Routerdan o'tgan barcha ilovalar bitta umumiy Gateway IP'ga ega bo'lib qoladi va IP bo'yicha ajratish ma'nosini yo'qotadi.
> - Yoki IP o'zgargan zahoti ilova `403 Forbidden` olib butunlay to'xtab qoladi.

---

### 🚀 IP o'rniga joriy qilingan 5 ta Enterprise xavfsizlik mexanizmi:

#### 1. Token Use Limit (`num_uses = 1`) — Bootstrap Token (Tavsiya etiladi)
- **Qanday ishlaydi:** Token yaratilganda `num_uses = 1` qilib beriladi.
- **Xavfsizlik kafolati:** Ilova (masalan, Java/Spring, Go, Node.js) ishga tushganda Vault'dan o'zining maxfiy kalitlarini xotiraga (RAM) o'qiydi. **O'qilishi bilan token Vault tomonidan shu zahoti yo'q qilinadi (avtomatik kuyadi)!**
- **Natija:** Agar kimdir keyinchalik ilova loglaridan yoki tranzit trafikdan tokenni o'g'irlasa ham, u 100% yaroqsiz bo'ladi (`403 invalid token`).

#### 2. Qisqa muddatli Dinamik TTL (Short-lived dynamic life cycle)
- Tokenlar oylar davomida amal qilmaydi.
- Test va deploy uchun `1h` yoki `24h` qisqa muddat belgilanadi.
- `renewable: false` orqali muddati sun'iy uzaytirilmaydigan cheklangan tokenlar yaratiladi.

#### 3. AppRole Dual-Key + Single-Use Secret-ID
- Ilova uchun ikkita alohida kalit ishlatiladi:
  - **Role ID:** Ilovaning o'zida yoki CI/CD deploy skriptida statik saqlanadi.
  - **Secret ID:** Deploy vaqtida orkestrator (CI/CD, Kubernetes pod init) tomonidan `num_uses=1` va `ttl=10m` bilan generatsiya qilinadi.
- Ilova Secret ID orqali 1 marta login qilib vaqtinchalik xotira tokenini oladi va Secret ID yaroqsiz bo'ladi.

#### 4. Response Wrapping (Cubbyhole — 1 martalik muhrlangan qadoq)
- Token yoki Secret-ID to'g'ridan-to'g'ri ochiq berilmaydi.
- Vault unga 10 daqiqalik muhrlangan **Wrapping Token** beradi:
  ```bash
  # Tranzitdan so'ng ilova 1 marta ochib oladi (unwrap):
  REAL_TOKEN=$(curl -k -s -X POST -H "X-Vault-Token: $WRAP_TOKEN" https://vault-srv.sarvartech.uz/v1/sys/wrapping/unwrap | jq -r .auth.client_token)
  ```
- **Xavfsizlik kafolati:** Agar xaker tranzit paytida qadoqni ochishga uringan bo'lsa, haqiqiy ilova ochish paytida `wrapping token already used` xatosini oladi. Tizim zudlik bilan audit log orqali hujumni aniqlaydi!

#### 5. Strict Granular ACL Policy (Eng asosiy himoya devori)
- Har bir tashkilot va servis qat'iy izolatsiyalangan:
  ```hcl
  # Masalan: Faqat Humo to'lov servisining kalitlarini o'qish mumkin
  path "secret/data/humo/payments" {
    capabilities = ["read"]
  }
  path "secret/metadata/humo/payments" {
    capabilities = ["read", "list"]
  }
  ```
- Ushbu policy biriktirilgan token boshqa hech bir tashkilot yoki qo'shni servisning kalitlariga zarracha ham yaqinlasha olmaydi!

