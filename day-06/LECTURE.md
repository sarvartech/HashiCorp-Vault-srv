# 📚 DAY 6: MA'RUZA MATNI
## Transit Secrets Engine: Encryption as a Service (EaaS)

---

### 1. Ma'lumotlarni Shifrlashdagi Eng Katta Xato

Tasavvur qiling, siz FinTech yoki E-Commerce ilovasini quryapsiz. Siz mijozlarning:
* Bank karta raqamlarini,
* Pasport ma'lumotlarini (JSHSHIR),
* Maxfiy tibbiy ma'lumotlarini saqlashingiz shart (PCI-DSS / GDPR talabi).

#### Odatda dasturchilar nima qiladi?
Dasturchi kod ichida AES kutubxonasini ishlatadi va `ENCRYPTION_KEY=mySecretKey123` ni `.env` faylga yozib qo'yadi.
**Natija:**
1. Agar server xakerlar qo'liga tushsa, ular bir vaqtning o'zida ham ma'lumotlar bazasini, ham `.env` fayldagi shifrlash kalitini o'g'irlashadi. Shifrlashdan hech qanday ma'no qolmaydi!
2. Shifrlash kalitini almashtirish (Rotation) deyarli imkonsiz bo'lib qoladi.

---

### 2. Encryption as a Service (EaaS) Falsafasi

Vault'ning **Transit Secret Engine**i butunlay boshqacha yondashuvni taklif qiladi:
> **"Vault o'z shifrlash kalitini HECH KIMGA bermaydi! Shifrlashni ham, de-shifrlashni ham Vault o'zi bajarib beradi."**

```
[ Dastur / Backend ] 
       │ 1. Mana bu karta raqamini shifrla: "8600 1234 5678 9999"
       ▼
┌──────────────────┐
│   VAULT CORE     │ ── 2. O'zining xavfsiz xotirasidagi kalit bilan shifrlaydi
└──────────────────┘
       │ 3. Qaytaradi: "vault:v1:7D8aKl9...==" (Ciphertext)
       ▼
[ Dastur / Backend ] ── 4. Shifrlangan matnni PostgreSQL bazasiga yozadi
```

Endi bazani kimdir to'liq o'g'irlab ketsa ham, u yerda faqat tushunarsiz `vault:v1:...` matnlari yotadi. Vault kalitisiz uni hech qanday superkompyuter ham ocha olmaydi.

---

### 3. Kalit Rotatsiyasi (Key Rotation) va Rewrap

Xavfsizlik talablariga binoan, har 6 oyda shifrlash kalitini yangilash tavsiya etiladi.
* Vault'da bitta buyruq bilan yangi kalit versiyasi (`v2`) yaratiladi.
* Shundan so'ng yangi kelgan barcha ma'lumotlar avtomatik `vault:v2:...` kaliti bilan shifrlanadi.
* **Eski ma'lumotlar nima bo'ladi?** 
  Vault'ning `rewrap` funksiyasi orqali eski shifrlangan ma'lumotlarni ochmasdan, to'g'ridan-to'g'ri yangi versiyaga qayta o'rab chiqish mumkin!
