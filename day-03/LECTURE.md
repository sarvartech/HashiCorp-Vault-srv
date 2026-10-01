# 📚 DAY 3: MA'RUZA MATNI
## Dinamik Sirlar (Dynamic Secrets) va Database Secrets Engine

---

### 1. Statik Sirlar va Dinamik Sirlar Farqi

Oldingi darsda o'rgangan KV-v2 sirimiz bu — **Statik Sir (Static Secret)**.
Siz unga parolni yozib qo'yasiz, u o'sha yerda yillab turaveradi.

#### Statik sirlarning muammolari:
1. **O'g'irlanish ehtimoli:** Agar dasturchi yoki xaker statik parolni bilib olsa, u paroldan xohlagancha foydalanishi mumkin.
2. **Kadrlar ketishi:** Xodim ishdan bo'shasa, u bilgan barcha ma'lumotlar bazasi parollarini zudlik bilan almashtirish (rotatsiya qilish) dahshatli bosh og'rig'i.
3. **Umumiy foydalanuvchi:** 10 ta mikroservis bitta umumiy `postgres` yoki `app_user` bilan bazaga ulanadi. Baza sekinlashsa, qaysi servis sababchi ekanini aniqlab bo'lmaydi.

#### HashiCorp Vault Yechimi: Dinamik Sirlar (Dynamic Secrets)

Dinamik sirlar oldindan mavjud bo'lmaydi. Ular dastur so'ragan paytda **on-demand (talabga binoan)** real vaqtda yaratiladi!

```
[ Dastur / Pod ] 
       │ 1. Menga DB paroli kerak (vault read database/creds/my-role)
       ▼
┌──────────────┐
│  VAULT CORE  │
└──────┬───────┘
       │ 2. PostgreSQL'ga ulanadi va buyruq yuboradi:
       │    CREATE USER "v-token-xyz123" WITH PASSWORD 'randomPass99!' VALID UNTIL '1h';
       │    GRANT SELECT ON ALL TABLES TO "v-token-xyz123";
       ▼
┌──────────────┐
│  POSTGRESQL  │
└──────────────┘
       │
       │ 3. Vault dasturga yangi username/password va Lease ID beradi.
       ▼
[ Dastur / Pod ] ── 4. Vaqtinchalik user bilan bazaga ulanadi (1 soat davomida)
```

1 soat (TTL) o'tgach, agar dastur ijarani uzaytirmasa (renew qilmasa), Vault bazaga kirib o'sha foydalanuvchini **avtomatik o'chirib tashlaydi (`DROP USER`)**.

---

### 2. Lease (Ijara) va TTL Tushunchasi

Vault'da har bir dinamik sirga **Lease (Ijara shartnomasi)** biriktiriladi.
Uning asosiy parametrlari:
* **Lease ID:** Masalan, `database/creds/readonly-role/h12345678...`. Har bir dinamik sirning unikal hujjati.
* **Lease Duration (TTL):** Sirning amal qilish muddati (masalan, 1h, 30m).
* **Renewable:** Ushbu muddatni uzaytirish mumkinmi yoki yo'qmi.

#### Ijarani boshqarish usullari:
1. **Renew (Uzaytirish):** Agar dastur uzoqroq ishlayotgan bo'lsa, har 45 daqiqada `vault lease renew <lease-id>` so'rovini yuborib turadi.
2. **Revoke (Muddatidan oldin bekor qilish):** Agar favqulodda vaziyat yuz bersa (xavfsizlik buzilsa), administrator `vault lease revoke <lease-id>` buyrug'ini berishi bilan Vault darhol bazadagi o'sha foydalanuvchini o'chiradi.
3. **Revoke-Prefix:** Butun tizimdagi barcha vaqtinchalik parollarni bir vaqtning o'zida bekor qilish: `vault lease revoke -prefix database/`.
