# 📚 DAY 5: MA'RUZA MATNI
## PKI Secrets Engine va mTLS (Ichki Sertifikatlar Markazi)

---

### 1. SSL/TLS Sertifikatlarining Bosh Og'rig'i

Har qanday korporativ muhitda (Kubernetes klasterlari, mikroservislar, ichki API'lar) shifrlangan TLS aloqasi shart.

#### An'anaviy muammolar:
1. **Muddati o'tib qolishi (Cert Outages):** Dunyodagi eng yirik kompaniyalar ham SSL sertifikat muddati tugab qolgani sababli ishlamay qoladi.
2. **Let's Encrypt chegarasi:** Let's Encrypt internetga ochiq domenlarni talab qiladi. Ichki lokal tarmoqdagi (`192.168.0.x` yoki `.internal`, `.local`) serverlar uchun ishlamaydi.
3. **OpenSSL orqali qo'lda yaratish:** `openssl.cnf` fayllari bilan ishlash, CSR yaratish, imzolash — juda ko'p xatolarga moyil va sekin jarayon.

---

### 2. Vault PKI Engine Arxitekturasi

Vault o'zini to'laqonli **Ichki Sertifikat Markazi (Private Certificate Authority - CA)** sifatida tutadi.

```
       ┌───────────────────────────────┐
       │     Vault Root CA (10 yil)    │
       └───────────────┬───────────────┘
                       │
       ┌───────────────▼───────────────┐
       │ Vault Intermediate CA (3 yil) │
       └───────────────┬───────────────┘
                       │ On-demand (1 soniyada)
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│ Microservice A   │        │ Microservice B   │
│ TLS Cert (30 kun)│        │ TLS Cert (30 kun)│
└──────────────────┘        └──────────────────┘
```

#### Afzalliklari:
1. **Bir soniyada tayyor:** Bitta API chaqiruvi bilan `.crt` va `.key` beriladi.
2. **Qisqa umrli sertifikatlar (Short-lived certs):** 1-2 yillik emas, 30 kunlik yoki 24 soatlik sertifikatlar berish mumkin. Agar kalit o'g'irlansa ham tezda kuchini yo'qotadi.
3. **Revocation List (CRL):** Agar servis xavf ostida qolsa, sertifikat bir zumda bekor qilinadi.

---

### 3. Mutual TLS (mTLS) va Zero-Trust

Oddiy HTTPS'da faqat mijoz serverni tekshiradi (server sertifikat ko'rsatadi).
**mTLS (Mutual TLS)** da esa:
* Server o'z sertifikatini ko'rsatadi (Mijoz serverni taniydi).
* **Mijoz ham o'z sertifikatini ko'rsatadi** (Server mijozni taniydi).

Tarmoqdagi hech kimga (hatto lokal tarmoq bo'lsa ham) ishonmaslik — **Zero-Trust Network Architecture** deyiladi. Vault PKI aynan shu arxitekturani avtomatlashtirishning asosiy poydevoridir.
