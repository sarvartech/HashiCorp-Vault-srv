# HashiCorp Vault Xavfsizlik va Foydalanish Qo'llanmasi

Ushbu serverda (**192.168.86.70**) HashiCorp Vault v2.1.1 eng yuqori xavfsizlik talablari asosida to'liq o'rnatildi va ishga tushirildi.

---

## 1. Asosiy Ma'lumotlar va Kirish

* **Vault Web UI Manzili:** [https://192.168.86.70:8200/ui](https://192.168.86.70:8200/ui)
* **Klaster manzili:** `https://192.168.86.70:8201`
* **Root Token:** `<YOUR_ROOT_TOKEN>`
* **Shamir Unseal Kalitlari (Jami: 3 ta, Ochish uchun lozim: 2 ta):**
  1. `<UNSEAL_KEY_1>`
  2. `<UNSEAL_KEY_2>`
  3. `<UNSEAL_KEY_3>`

> **Muhim eslatma:** Serverdagi `/root/vault_credentials.json` fayli faqat `root` foydalanuvchisi uchun (chmod 600) ruxsat bilan saqlangan. Mahalliy papkangizda ham [vault_credentials.json](file:///c:/Users/user/Documents/vault-vrs/vault_credentials.json) mavjud.

---

## 2. 4 Qatlamli Xavfsizlik Arxitekturasi (Qanday himoyalangan?)

### 1-Qatlam: Tarmoq Shifrlanishi (TLS / HTTPS in Transit)
* Serverda maxsus xususiy **Root Certificate Authority (CA)** va 2048-bit **Server SSL Sertifikati** yaratildi.
* SAN (Subject Alternative Names): `192.168.86.70`, `127.0.0.1`, `vault.local`, `localhost`.
* Tarmoq orqali o'tayotgan barcha ma'lumotlar (so'rovlar, parollar, API tokenlar) TLS 1.2+ shifrlangan holda uzatiladi. Tarmoqdagi snifferlar yoki 3-shaxslar ma'lumotni o'qiy olmaydi.

### 2-Qatlam: Diskdagi Shifrlash (Encryption at Rest & Raft Storage)
* Vault'ning **Raft Integrated Storage** tizimi ishlatildi (`/opt/vault/data`).
* Barcha ma'lumotlar diskka yozilishidan oldin **AES-256-GCM** shifrlash algoritmi orqali shifrlanadi.
* Server administratori yoki diskdan nusxa ko'chirgan shaxs fayllarni ochsa ham, ularni o'qiy olmaydi (shifrlangan baytlar ketma-ketligi ko'rinadi).
* `mlock` faollashtirilgan — ma'lumotlar operativ xotiradan (RAM) diskdagi Swap xotiraga tushmaydi.

### 3-Qatlam: Shamir's Secret Sharing (Muhrlash va Ochish)
* Vault server qayta o'chib yonganda (reboot) avtomatik **Sealed (Muhrlangan)** holatda bo'ladi.
* Hech bir yagona tizim administratori (Sysadmin/DevOps) o'zboshimchalik bilan serverni ocholmasligi uchun unseal kalitlari 3 bo'lakka bo'lindi.
* Serverni ochish uchun kamida **2 ta kalit** kerak (masalan, biri Xavfsizlik bo'limi boshlig'ida, biri DevOps rahbarida bo'ladi).

### 4-Qatlam: Rol va Siyosatga Asoslangan Ruxsat (Least Privilege RBAC) & Audit Log
* **Root token faqat dastlabki sozlash uchun** ishlatiladi. Ish jarayonida root tokendan foydalanilmaydi.
* Har bir dastur (CI/CD, Backend) va har bir xodim (DevOps, Dev) uchun alohida ruxsat siyosati (Policy) yaratiladi.
* **Audit Device:** `/var/log/vault/vault_audit.log` faylida kim, qachon, qaysi IP'dan, qaysi sekretni so'ragani yozib boriladi. Eng muhimi: log faylda barcha maxfiy kalit va parollar **HMAC-SHA256** orqali xeshlanadi, hatto log faylni ochgan odam ham parollarni ko'ra olmaydi!

---

## 3. Web UI orqali Boshqarish

1. Brauzeringizda oching: [https://192.168.86.70:8200/ui](https://192.168.86.70:8200/ui)
2. Brauzer o'zimiz yaratgan ichki CA sertifikatini ko'rsatadi:
   * **Windows'ga CA'ni qo'shish (ixtiyoriy):** [vault_ca.crt](file:///c:/Users/user/Documents/vault-vrs/vault_ca.crt) faylini ikki marta bosing -> `Install Certificate` -> `Local Machine` -> `Trusted Root Certification Authorities` tanlab o'rnating. Shunda ogohlantirish yo'qoladi.
   * Yoki brauzerda `Advanced` -> `Proceed to 192.168.86.70 (unsafe)` bosing.
3. Kirish usullari:
   * **Token:** `<YOUR_ROOT_TOKEN>` (Administrator huquqi)
   * **Username:** `dev_user`, parol: `DevUserPass2026!` (Faqat dev ruxsati bor foydalanuvchi)

---

## 4. Real Sinovdan O'tgan Test Natijalari

Siz uchun maxsus tayyorlangan [test_vault.py](file:///c:/Users/user/Documents/vault-vrs/test_vault.py) skripti orqali ruxsatlar tekshirildi:

```text
1. Root Token Access:
   - secret/prod/database: OK (200)

2. AppRole Access (backend-service):
   - secret/prod/database: OK (200 - ruxsat berilgan)
   - secret/dev/database:  403 Forbidden (BLOCKED BY POLICY - bloklandi!)

3. Developer User Access (dev_user):
   - secret/dev/database:  OK (200 - ruxsat berilgan)
   - secret/prod/database: 403 Forbidden (BLOCKED BY POLICY - bloklandi!)
```

---

## 5. Dasturlar va CI/CD bilan Bog'lash (AppRole Metodi)

Dasturlar (Python, Node.js, Java, Golang) yoki GitLab CI/CD, GitHub Actions hech qachon qattiq kodlangan (hardcoded) parollardan foydalanmasligi kerak. Buning o'rniga **AppRole** ishlatiladi:

1. **Role ID:** `942401ef-6873-efcd-2f90-c84cf0bfc53c`
2. **Secret ID:** `262646c9-0c7a-f662-e26f-6ab17e304a59`

### Python orqali sekretni o'qish namunasi:
```python
import requests

VAULT_URL = "https://192.168.86.70:8200"
ROLE_ID = "942401ef-6873-efcd-2f90-c84cf0bfc53c"
SECRET_ID = "262646c9-0c7a-f662-e26f-6ab17e304a59"

# 1. AppRole orqali vaqtinchalik xavfsiz token olish (1 soatlik)
login_res = requests.post(
    f"{VAULT_URL}/v1/auth/approle/login",
    json={"role_id": ROLE_ID, "secret_id": SECRET_ID},
    verify="vault_ca.crt"
)
token = login_res.json()["auth"]["client_token"]

# 2. Sekretni o'qish
secret_res = requests.get(
    f"{VAULT_URL}/v1/secret/data/prod/database",
    headers={"X-Vault-Token": token},
    verify="vault_ca.crt"
)
db_credentials = secret_res.json()["data"]["data"]
print("Database User:", db_credentials["username"])
print("Database Password:", db_credentials["password"])
```

---

## 6. Serverni Boshqarish Buyruqlari (CLI)

Serverga SSH (`ssh sarvar@192.168.86.70`) orqali kirganingizda:

### Statusni tekshirish:
```bash
vault status
```

### Agar server o'chib-yonsa, uni ochish (Unseal):
```bash
vault operator unseal <UNSEAL_KEY_1>
vault operator unseal <UNSEAL_KEY_2>
```

### Yangi sekret qo'shish:
```bash
export VAULT_TOKEN="<YOUR_ROOT_TOKEN>"
vault kv put secret/my-project/api-key token="ABC-123-SECRET"
```

### Sekretni o'qish:
```bash
vault kv get secret/my-project/api-key
```

### Yangi foydalanuvchi qo'shish:
```bash
vault write auth/userpass/users/akmal password="Parol123!" policies="dev-policy"
```

### Yangi Siyosat (Policy) yaratish:
Masalan, `/tmp/marketing.hcl` yaratib:
```hcl
path "secret/data/marketing/*" {
  capabilities = ["create", "read", "update"]
}
```
Uni yuklash:
```bash
vault policy write marketing-policy /tmp/marketing.hcl
```
