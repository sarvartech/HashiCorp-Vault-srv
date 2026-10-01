# 🛠️ DAY 7: AMALIY QO'LLANMA (LAB GUIDE)
## Audit Logging, Raft Snapshot Zaxiralash va Favqulodda Tiklash

Kursning so'nggi kunida biz ishlab chiqarish tizimi uchun Audit jurnalini yoqamiz, butun Vault ma'lumotlar bazasining zaxira nusxasini (Snapshot) olamiz va uni qayta tiklashni (Disaster Recovery) sinaymiz.

---

### 1-Qadam: Audit Device (Audit Log) Yoqish

Vault'da xavfsizlik auditini yoqmasdan turib uni ishlab chiqarishga chiqarish qat'iyan man etiladi.

```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="<ROOT_TOKEN>"

# Log papkasini yaratish va huquq berish
sudo mkdir -p /var/log/vault
sudo chown -R vault:vault /var/log/vault

# File audit qurilmasini faollashtirish
vault audit enable file file_path=/var/log/vault/vault_audit.log

# Faolligini tekshirish
vault audit list
```

---

### 2-Qadam: Audit Logning Shifrlanganligini (HMAC) Tekshirish

Keling, biror sirni o'qib ko'ramiz va logda nima yozilishini tekshiramiz:

```bash
vault kv get secret/production/database

# Log faylining oxirgi qatorini ko'ramiz
sudo tail -n 1 /var/log/vault/vault_audit.log | jq
```

> **Diqqat qiling:** Logda parollar yoki tokenlar ochiq ko'rinmaydi! Barcha maxfiy ma'lumotlar `hmac-sha256:abcd...` shaklida shifrlangan bo'ladi. Tizim administratori ham parolni logdan ko'ra olmaydi.

---

### 3-Qadam: Raft Integrated Storage Holatini Ko'rish

```bash
vault operator raft list-peers
```
Siz klasterdagi tugunlar (Node ID, manzil, holat - Leader/Follower) ro'yxatini ko'rasiz.

---

### 4-Qadam: Zaxira Nusxa (Raft Snapshot) Olish

Butun Vault klasterining (barcha sirlar, siyosatlar, konfiguratsiyalar) bir zumlik to'liq nusxasini olamiz:

```bash
vault operator raft snapshot save /home/doker/vault_backup_$(date +%F).snap

ls -lh /home/doker/*.snap
```
> Ushbu `.snap` fayli barcha ma'lumotlarni o'zida saqlaydi (albatta, shifrlangan holatda!).

---

### 5-Qadam: Favqulodda Tiklash (Disaster Recovery Test)

Keling, halokat holatini simulyatsiya qilamiz. Tasavvur qiling, qaysidir dasturchi muhim ma'lumotni o'chirib yubordi:

```bash
# Sirni o'chiramiz
vault kv destroy -versions=1,2 secret/production/database
vault kv get secret/production/database
```
> Ma'lumot yo'qoldi!

Endi zaxira faylimizdan butun tizimni oldingi holatiga qaytaramiz:

```bash
vault operator raft snapshot restore -force /home/doker/vault_backup_*.snap
```

Qayta tiklangach, sirni yana tekshirib ko'ramiz:
```bash
vault kv get secret/production/database
```
🎉 **Ma'lumotlarimiz to'liq qayta tiklandi!**

---

### 6-Qadam: Root Tokendan Xalos Bo'lish (Root Token Revoke)

Barcha sozlashlar (AppRole, Audit, Foydalanuvchilar) yakunlangach, xavfsizlik nuqtai nazaridan Root Token bekor qilinishi lozim:

```bash
# Ehtiyot bo'ling: bu amal qaytarilmaydi! Boshqa admin hisobingiz borligiga ishonch hosil qiling!
vault token revoke <ROOT_TOKEN>
```

---

### 🏆 TABRIKLAYMIZ!
Siz **"7 Kunda Mastering HashiCorp Vault"** kursini muvaffaqiyatli yakunladingiz! Endi siz:
* Vault arxitekturasini,
* KV-v2 va versiyalashni,
* Vaqtinchalik dinamik ma'lumotlar bazasi hisoblarini,
* AppRole va eng kam imtiyozli HCL siyosatlarini,
* Ichki CA va SSL/TLS sertifikatlarini boshqarishni,
* Transit orqali dastur ma'lumotlarini shifrlashni (EaaS),
* Raft HA, Audit va Disaster Recovery mexanizmlarini to'liq o'zlashtirdingiz!
