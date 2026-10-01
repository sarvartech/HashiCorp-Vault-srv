# 📚 DAY 1: MA'RUZA MATNI
## HashiCorp Vault Arxitekturasi, Barrier va Shamir's Secret Sharing

---

## 1. Kirish: Vault Nima va U Qachon Yaratilgan?

**HashiCorp Vault** — bu maxfiy ma'lumotlarni (parollar, API kalitlari, SSL/TLS sertifikatlari) xavfsiz saqlash, ularga kirish huquqini qat'iy nazorat qilish va ularni talabga binoan shifrlash uchun mo'ljallangan markazlashtirilgan dasturiy ta'minotdir.

* **Yaratilish tarixi:** HashiCorp Vault serverining birinchi talqini (`v0.1.0`) 2015-yil aprel oyida ommaga taqdim etilgan.
* **Barqaror talqin (Vault 1.0):** 2018-yil 4-dekabrda tizim to'liq yetilib, yuqori yuklamalarga mos 1.0 versiyasi chiqarildi.
* **Til:** Vault to'liq **Go (Golang)** tilida yozilgan bo'lib, bitta ixcham binary fayldan iborat.

---

## 2. Vault'dan Oldin Maxfiy Ma'lumotlar Qanday Saqlangan?

Vault paydo bo'lishidan oldin sirlarni saqlashda quyidagi "eski maktab" usullaridan foydalanilgan:

1. **Hardcoded Secrets (Kod ichiga yozib ketish) ❌:**
   * Dasturchilar parollarni to'g'ridan-to'g'ri kod ichiga (`const DB_PASS = "pass123"`) yozib ketishgan. Kod Git/GitHub'ga chiqib ketsa, loyiha butunlay fosh bo'lgan.
2. **Plain Text `.env` va Config fayllar 📄:**
   * Sirlar serverda ochiq matn ko'rinishida saqlangan. Serverga kirgan har qanday odam `cat .env` orqali hamma sirlarni bilib olgan.
3. **Operatsion tizim o'zgaruvchilari (Environment Variables) 💻:**
   * `export DB_PASS="my-secret"`. Ammo serverda `printenv` yozgan har qanday skript yoki foydalanuvchi ularni ko'ra olgan.
4. **Shifrlangan fayllar (Ansible Vault, git-crypt) 🔐:**
   * Fayllar shifrlangan, lekin uni ochuvchi bitta umumiy "Master kalit" baribir serverda ochiq qolgan (xuddi uy kalitini gilam ostiga yashirishdek).

> **Xulosa:** Vault'dan oldin maxfiy ma'lumotlar serverlardagi oddiy matnli fayllarda (`.env`), operatsion tizim oʻzgaruvchilarida yoki dastur kodining ichida ochiq (shifrlanmagan) holatda saqlangan. Bu tizimni tashqi xakerlik hujumlariga va ichki xodimlar sababli ma'lumotlar sizib chiqishiga oʻta zaif qilib qoʻygan.

---

## 3. Vault Free (Bepul) yoki Pullikmi?

Vault **Freemium** modeli asosida tarqatiladi:

| Xususiyati | Vault Community (Bepul / Open Source) | Vault Enterprise (Pullik) |
| :--- | :--- | :--- |
| **Narxi** | **Mutlaqo bepul** | Foydalanish hajmiga qarab (yiliga minglab $) |
| **Qayerda ishlaydi** | O'zingizning serveringizda (On-Premises / Cloud) | O'zingizda yoki HashiCorp bulutida (HCP) |
| **Asosiy imkoniyatlar** | KV-v2, Dinamik bazalar, PKI, Transit EaaS, CLI/UI/API | Bepul talqindagi barcha funksiyalar |
| **Korporativ imkoniyatlar**| Mavjud emas | Multi-region replikatsiya, Namespaces, 24/7 SLA yordam |

> **Muhim litsenziya eslatmasi:** 2023-yil avgust oyida HashiCorp Vault litsenziyasini **BSL 1.1 (Business Source License)** ga o'zgartirdi. Bu siz o'z loyihalaringiz va kompaniyangiz ichida undan **bepul foydalanishingiz mumkinligini**, faqat Vault kodini olib unga raqobatchi pullik bulutli xizmat yaratib sotish taqiqlanganini bildiradi.

---

## 4. Vault Nima Muammoni Hal Qiladi?

HashiCorp Vault IT olamidagi eng ogʻriqli muammo — **"Secret Sprawl"** (sirlarning har tomonga tarqalib ketishi) muammosini hal qiladi.
* **Yagona Seyf:** Parollar, tokenlar va sertifikatlarni bitta shifrlangan joyda jamlaydi.
* **Dinamik Sirlar:** Parollarni qo'lda yangilash azobidan qutqaradi — talabga ko'ra bir martalik, o'z-o'zidan o'chib ketuvchi vaqtinchalik hisoblar ochadi.
* **Audit:** Har bir kalitni kim, qachon, qaysi IP'dan olganini soniyasigacha hisoblab boradi.

---

## 5. Hayotiy Metafora: Vault Serverini Qanday Jismoniy Obyekt Bilan Solishtirish Mumkin?

Vault'ni his qilish uchun eng mukammal jismoniy obyekt — **"Zamonaviy Bank Seyfi (Depozitariy)"**:

1. **Shamir Kalitlari (Unseal):** Bu seyf bitta kalit bilan ochilmaydi. Uning eshigini ochish uchun bir nechta bank boshqaruvchilari o'z kalitlarini (masalan, 5 kishidan 3 nafari) bir vaqtda burashlari shart.
2. **HCL Policies (Ruxsatnomalar):** Seyf xonasiga kirganingizda, shaxsingiz tasdiqlanadi va sizga faqat ruxsatnomangiz yetadigan aniq bitta yacheyka ochiladi.
3. **Audit Loglar:** Xonadagi videokameralar va kirish-chiqish daftarlari har bir harakatni yozib boradi.
4. **Dinamik Sirlar:** Ba'zi qutilar xuddi taymerli bir martalik qulflardek ishlaydi — 15 daqiqadan so'ng o'z-o'zidan yopiladi.

---

## 6. Nega Vault Shunchaki Vosita Emas, Balki "Sug'urta"?

Bugungi kunda xakerlar GitHub yoki serverlarni qoʻlda buzib oʻtirmaydi; ular **maxsus botlar** yordamida ochiq `.env` fayllar yoki API kalitlarni internet bo'ylab soniyalar ichida skanerlaydi.
* Agar bulutli (AWS / GCP / OpenAI) API kalitingiz chiqib ketsa, botlar 5 daqiqada sizning hisobingizdan kriptovalyuta mayning qilib, **minglab dollarlik qarz** yozib qo'yishi mumkin.
* Mijozlar ma'lumotlari sizib chiqsa — sud jarayonlari va katta jarimalar kelib chiqadi.
Vault sizga parollaringizni hech qachon ochiq qoldirmasdan, loyiha kattalashsa ham xotirjam uxlash kafolatini (sug'urtasini) beradi.

---

## 7. Kim O'rnatadi va Boshqaradi?

Kompaniyalarda Vault serverini sozlash, monitoring qilish va xavfsizligini ta'minlash bevosita **DevOps Engineer** yoki **DevSecOps Engineer** mutaxassisi vazifasiga kiradi. Dasturchilar (Developers) esa tayyor Vault'dan API va SDK orqali o'z ilovalariga sirlarni tortib olish uchun foydalanadilar.

---

## 8. Kichik Loyihalarga Ham Kerakmi Yoki Faqat Banklarga?

* **Kichik loyihalar (1 dasturchi, oddiy monolit):** Dastlabki bosqichda Vault shart emas. Yaxshi himoyalangan serverdagi `.env` fayl yetarli bo'ladi. Vault o'zining arxitekturasi bilan kichik loyihaga ortiqcha yuklama (**overkill**) bo'lishi mumkin.
* **O'rta va yirik loyihalar (Mikroservislar, bir nechta server, jamoada 3+ dasturchi, CI/CD):** Vault zudlik bilan zaruriyatga aylanadi!

---

## 9. Vault Serveri Uchun Nimalar Kerak? (Tizim Talablari)

Ishlab chiqarish (Production) muhitida to'g'ri ishga tushirish uchun 3 ta asosiy komponent talab qilinadi:

### 1. Infratuzilma (Infrastructure):
* **Operatsion tizim:** Linux (Ubuntu Server 22.04/24.04 yoki RHEL/Rocky Linux) — sanoat standarti.
* **Minimal resurslar:** 2 vCPU va 4 GB RAM (Vault asosan RAM xotirada ishlagani uchun operativ xotira tezligi va hajmi muhim).
* **Tarmoq portlari:** 
  * `8200` — Foydalanuvchilar, dasturlar va Web UI uchun (API).
  * `8201` — Klaster ichidagi serverlararo aloqa (Cluster mTLS).

### 2. Kriptografik Talablar (Security):
* **TLS/SSL Sertifikati:** HTTP orqali parollarni ochiq uzatish man etiladi. HTTPS majburiy.
* **`mlock` huquqi:** Vault xotiradagi parollarni Linux swap xotirasiga chiqarmasligi uchun `cap_ipc_lock=+ep` talab qilinadi.

### 3. Ma'lumotlar Ombori (Storage Backend):
* **Integrated Raft Storage:** Vault'ning o'zining ichki ombori. Qo'shimcha baza talab qilmaydi, hozirda eng tavsiya etiladigan zamonaviy yechim.
* Yoki tashqi omborlar: Consul, PostgreSQL, AWS S3.

---

## 10. Vault Arxitekturasi: Ichki Mexanizm

```
                  ┌───────────────────────────────┐
                  │    Foydalanuvchi / Dastur     │
                  │   (CLI / Web UI / REST API)   │
                  └───────────────┬───────────────┘
                                  │ (TLS HTTPS - Port 8200)
                                  ▼
┌─────────────────────────── HTTP API ───────────────────────────┐
│                                                                 │
│  ┌──────────────────── Cryptographic Barrier ────────────────┐  │
│  │                                                           │  │
│  │  ┌──────────────┐   ┌────────────────┐   ┌─────────────┐  │  │
│  │  │ Auth Methods │──>│ Engine Router  │──>│ Audit Logs  │  │  │
│  │  │ (AppRole,    │   │ (KV, PKI,      │   │ (Syslog,    │  │  │
│  │  │  Userpass)   │   │  Database)     │   │  File)      │  │  │
│  │  └──────────────┘   └────────────────┘   └─────────────┘  │  │
│  │                                                           │  │
│  └──────────────────────────────┬────────────────────────────┘  │
│                                 │ (AES-256-GCM Shifrlash)       │
└─────────────────────────────────┼───────────────────────────────┘
                                  ▼
                 ┌─────────────────────────────────┐
                 │         Storage Backend         │
                 │   (Integrated Raft / File / DB) │
                 └─────────────────────────────────┘
```

### Shamir's Secret Sharing va Unseal Jarayoni:

Server o'chib yonganda (reboot) Vault doimo **Sealed (Qulflangan)** holatda bo'ladi.
Diskdagi shifrlangan ma'lumotlarni ochish uchun **Master Key** kerak. Shamir algoritmi orqali bu kalit bo'laklarga ajratiladi:

```
                  ┌────────────────────────┐
                  │       Master Key       │
                  └───────────┬────────────┘
                              │ (Shamir algoritmi)
          ┌─────────┬─────────┼─────────┬─────────┐
          ▼         ▼         ▼         ▼         ▼
       Kalit 1   Kalit 2   Kalit 3   Kalit 4   Kalit 5
```

* **Key Shares ($N=5$):** Jami bo'laklar soni.
* **Key Threshold ($T=3$):** Ochish uchun talab qilinadigan minimal bo'laklar soni.
* Kamida 3 ta kalit kiritilganda, Vault RAM xotirada Master Key'ni tiklaydi, shifrlash kalitini ochadi va o'zini **Unsealed** holatiga o'tkazadi!
