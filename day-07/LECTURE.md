# 📚 DAY 7: MA'RUZA MATNI
## Production Hardening, Raft High Availability (HA) va Auto-Unseal

---

### 1. Production Xavfsizlik Talablari (Hardening Checklist)

Vault'ni ishlab chiqarish (Production) muhitida ishlatishda quyidagi oltin qoidalarga rioya qilish shart:

| Talab | Nima uchun muhim? |
| :--- | :--- |
| **1. TLS Majburiy** | HTTP orqali barcha parollar ochiq o'tadi. Faqat HTTPS / TLS 1.2+ ruxsat etiladi. |
| **2. `mlock` yoqilgan bo'lishi** | Linux operativ xotiradagi (RAM) maxfiy kalitlarni diskdagi Swap faylga chiqarib tashlamasligi kerak. |
| **3. Root Token Revoke** | Klaster ishga tushgach, dastlabki root token bekor qilinishi shart! |
| **4. Audit Logging Yoqilgan** | Har bir kirish va so'rov yozib borilishi lozim. Agar audit qurilmasi to'lib qolsa yoki ishlamasa, Vault yangi so'rovlarni qabul qilmay to'xtaydi (Fail-closed xavfsizlik modeli). |
| **5. Doimiy Zaxira (Snapshots)** | Raft snapshot har kuni avtomatlashtirilgan tarzda olinishi va alohida xavfsiz serverga yuborilishi kerak. |

---

### 2. High Availability (HA) va Integrated Raft Storage

Vault klasteri odatda **3 ta yoki 5 ta tugundan (node)** iborat bo'ladi (Raft konsensus algoritmi toq sonli tugunlarni talab qiladi):

```
       ┌────────────────────────┐
       │   Load Balancer (HA)   │
       └───────────┬────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌────────┐     ┌────────┐     ┌────────┐
│ Node 1 │     │ Node 2 │     │ Node 3 │
│ ACTIVE │     │STANDBY │     │STANDBY │
└────────┘     └────────┘     └────────┘
    ▲              ▲              ▲
    └──────────────┴──────────────┘
         Raft Replication (Log)
```

* **Active Node:** Faqat 1 ta tugun barcha yozish va o'qish so'rovlarini to'g'ridan-to'g'ri qabul qiladi.
* **Standby Nodes:** Qolgan tugunlar faol tugun bilan ma'lumotlarni sinxronlashtirib turadi. Agar Active tugun qulasa, Standby tugunlardan biri 1-2 soniya ichida o'zini yangi Active etib saylaydi.

---

### 3. Auto-Unseal Mexanizmi

Eslang, Day 1 da biz Vault'ni qo'lda 3 ta Shamir kalit bilan ochgan edik (`vault operator unseal`).
Lekin katta korporatsiyalarda 50 ta server kechasi qayta yuklansa, har biriga qo'lda kalit kiritib chiqish — noqulay va kechikishlarga sabab bo'ladi.

**Auto-Unseal Yechimi:**
Master Key'ni ochish vazifasi tashqi ishonchli apparat yoki xizmatga topshiriladi:
* AWS KMS / Azure Key Vault / GCP KMS
* Yoki alohida markaziy Vault klasteri (Transit Auto-Unseal)

Server qayta yoqilganda, u KMS'ga murojaat qilib, avtomatik ravishda Unseal bo'ladi — hech qanday inson aralashuvi talab qilinmaydi!
