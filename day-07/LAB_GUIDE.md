# 🛠️ DAY 7: AMALIY QO'LLANMA (LAB GUIDE)
## 🔥 3 TA SERVERDA PRODUCTION RAFT HA KLASTERNI SOZLASH VA FAILOVER TEST

Bugungi amaliyotda biz korporativ banklar va yirik IT kompaniyalar talabiga mos bo'lgan **3 ta mustaqil tugundan iborat Raft HA Klasterini** noldan quramiz, tugunlarni birlashtiramiz, Nginx Load Balancerni ulaymiz va jonli ravishda serverni "o'chirib" failover'ni sinaymiz!

---

### 🖥️ Infratuzilma Rejasi (3 ta VM / Server):

| Server Nomi | IP Manzili | Roli | API Manzili (`api_addr`) | Raft Manzili (`cluster_addr`) |
| :--- | :--- | :--- | :--- | :--- |
| **vault-node1** | `192.168.10.11` | Birlamchi Leader | `http://192.168.10.11:8200` | `http://192.168.10.11:8201` |
| **vault-node2** | `192.168.10.12` | Standby Follower | `http://192.168.10.12:8200` | `http://192.168.10.12:8201` |
| **vault-node3** | `192.168.10.13` | Standby Follower | `http://192.168.10.13:8200` | `http://192.168.10.13:8201` |

*(Izoh: Agar bitta jismoniy mashinada sinayotgan bo'lsangiz, 3 ta alohida Multipass VM yoki alohida portlar orqali ham xuddi shu mantiqda bajarishingiz mumkin).*

---

### 1-Qadam: Har Bir Tugunda Konfiguratsiyani Sozlash

Har bir serverda `/etc/vault.d/vault.hcl` faylini ochib, quyidagicha to'ldiramiz:

#### 📌 NODE 1 (`192.168.10.11` da):
```hcl
storage "raft" {
  path    = "/opt/vault/data"
  node_id = "node1"
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_disable   = 1    # Ishlab chiqarishda TLS sertifikat ulanadi
}

api_addr      = "http://192.168.10.11:8200"
cluster_addr  = "http://192.168.10.11:8201"
ui            = true
disable_mlock = false
```

#### 📌 NODE 2 (`192.168.10.12` da):
```hcl
storage "raft" {
  path    = "/opt/vault/data"
  node_id = "node2"
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_disable   = 1
}

api_addr      = "http://192.168.10.12:8200"
cluster_addr  = "http://192.168.10.12:8201"
ui            = true
disable_mlock = false
```

#### 📌 NODE 3 (`192.168.10.13` da):
```hcl
storage "raft" {
  path    = "/opt/vault/data"
  node_id = "node3"
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_disable   = 1
}

api_addr      = "http://192.168.10.13:8200"
cluster_addr  = "http://192.168.10.13:8201"
ui            = true
disable_mlock = false
```

Barcha serverlarda xizmatni yoqing:
```bash
sudo systemctl restart vault
sudo systemctl enable vault
```

---

### 2-Qadam: NODE 1 ni Initsializatsiya Qilish va Unseal Qilish

Klasterda faqat **1-tugun** initsializatsiya qilinadi! Qolgan tugunlar esa unga ulanadi.

```bash
# Node 1 da turib bajaramiz:
export VAULT_ADDR="http://127.0.0.1:8200"

# Initsializatsiya:
vault operator init -key-shares=5 -key-threshold=3
```
> [!IMPORTANT]
> Chiqqan 5 ta **Unseal Key** va 1 ta **Initial Root Token**ni xavfsiz joyga saqlab oling! Ushbu kalitlar barcha 3 ta tugun uchun yagona bo'ladi.

Endi Node 1 ni muhrdan ochamiz (3 ta kalit bilan):
```bash
vault operator unseal  # 1-kalit
vault operator unseal  # 2-kalit
vault operator unseal  # 3-kalit

vault status
```
✅ `HA Enabled: true` va `Mode: active` ekanligiga ishonch hosil qiling!

---

### 3-Qadam: NODE 2 va NODE 3 ni Klasterga Birlashtirish (`raft join`)

Endi qolgan ikkita serverni Leader tugunga ulaymiz:

#### 📌 NODE 2 da:
```bash
export VAULT_ADDR="http://127.0.0.1:8200"

# 1-tugunga ulanish buyrug'i:
vault operator raft join http://192.168.10.11:8200

# Muvaffaqiyatli ulangach, Node 2 ni ham xuddi o'sha Shamir kalitlari bilan Unseal qilamiz:
vault operator unseal  # (1-kalit)
vault operator unseal  # (2-kalit)
vault operator unseal  # (3-kalit)

vault status
```
*Natija:* `Mode: standby` bo'lib turadi. Bu to'g'ri!

#### 📌 NODE 3 da:
```bash
export VAULT_ADDR="http://127.0.0.1:8200"

# 1-tugunga ulanish:
vault operator raft join http://192.168.10.11:8200

# Shamir kalitlari bilan Unseal qilish:
vault operator unseal
vault operator unseal
vault operator unseal

vault status
```

---

### 4-Qadam: Klaster Kvorumi va Ishtirokchilarni Tekshirish

Node 1 da turib klasterdagi barcha tugunlar holatini ko'ramiz:

```bash
export VAULT_TOKEN="<ROOT_TOKEN>"
vault operator raft list-peers
```

**Kutilgan Natija (3 ta Voter):**
```text
Node     Address               State       Voter
----     -------               -----       -----
node1    192.168.10.11:8201    leader      true
node2    192.168.10.12:8201    follower    true
node3    192.168.10.13:8201    follower    true
```
🎉 **Tabriklaymiz! 3 ta tugunli to'liq Quorumga ega Raft HA Klasteri barpo etildi!**

---

### 5-Qadam: Nginx Load Balancerni Sozlash

Mijozlar alohida IP'lar bilan emas, bitta yagona manzil bilan ishlashi uchun Nginx'da sog'liqni tekshiruvchi upstream sozlaymiz:

```nginx
upstream vault_cluster {
    server 192.168.10.11:8200;
    server 192.168.10.12:8200;
    server 192.168.10.13:8200;
}

server {
    listen 80;
    server_name vault.company.uz;

    location / {
        proxy_pass http://vault_cluster;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_next_upstream error timeout http_502 http_503 http_504;
    }
}
```

---

### 6-Qadam: 💥 KATTA AVARIYA VA FAILOVER TESTI!

Keling, haqiqiy avariyaning oldini olish qobiliyatini tekshiramiz.

#### 1. Yangi ma'lumot yozamiz:
```bash
vault kv put secret/company/database password="super_secret_production_password"
```

#### 2. Node 1 (Active Leader) ni ataylab o'chiramiz:
```bash
# Node 1 terminalida:
sudo systemctl stop vault
```

#### 3. Darhol Node 2 yoki Node 3 da tekshiramiz:
```bash
# Node 2 da:
vault status
```
Ko'rasizki, Node 2 yoki Node 3 **1 soniya ichida o'zini yangi LEADER etib sayladi!**
```text
HA Enabled: true
Mode: active     <-- Node 2 avtomatik Leader bo'ldi!
```

#### 4. Ma'lumot yo'qolmaganini tekshiramiz:
```bash
vault kv get secret/company/database
```
Ma'lumotlar to'liq joyida va xizmat 1 soniyaga ham to'xtamadi!

#### 5. O'chgan Node 1 ni qayta yoqamiz:
```bash
# Node 1 da:
sudo systemctl start vault
# (Agar auto-unseal bo'lmasa, unseal qilinadi)
vault status
```
Node 1 klasterga yangi Leader sifatida emas, balki intizomli **Follower (Standby)** sifatida qaytib qo'shiladi!

---

### 7-Qadam: Klaster Zaxira Nusxasini (Raft Snapshot) Olish

Butun 3 ta tugunning to'liq arxivini bitta faylga saqlab olamiz:

```bash
vault operator raft snapshot save /backups/vault_ha_backup_$(date +%F).snap

ls -lh /backups/*.snap
```

---

### 8-Qadam: Root Tokendan Xalos Bo'lish (Production Ready!)

```bash
vault token revoke <ROOT_TOKEN>
```

---

### 🏆 TABRIKLAYMIZ!
Siz 7 kunlik intensiv challengeni muvaffaqiyatli yakunladingiz! 
Endi siz:
* Oddiy parollardan qutulib, butun tashkilot uchun xavfsiz Zero-Trust arxitekturasini qura olasiz;
* 3 ta serverdan iborat yuqori bardoshli **Raft HA Klasterini** ishlab chiqarish (Production) darajasida mustaqil administratsiya qila olasiz!
