# 🛠️ DAY 1: AMALIY QO'LLANMA (LAB GUIDE)
## Vault Serverini O'rnatish, Konfiguratsiya va Unseal Qilish

Ushbu amaliyotda siz o'zingizning Ubuntu 24.04 serveringizda Vault'ni o'rnatasiz, `vault.hcl` konfiguratsiya faylini yozasiz, tizim xizmatini ishga tushirasiz va Shamir kalitlari bilan birinchi ochish (Unseal) amalini bajarasiz.

---

### 1-Qadam: HashiCorp Rasmiy Repozitoriysini Qo'shish va O'rnatish

Serveringiz terminalida quyidagi buyruqlarni ketma-ket bajaring:

```bash
# 1. Zarur yordamchi paketlarni o'rnatish
sudo apt-get update && sudo apt-get install -y curl gpg lsb-release

# 2. HashiCorp GPG rasmiy kalitini yuklash
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# 3. APT manbalariga repozitoriyni qo'shish
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# 4. Vault paketini o'rnatish
sudo apt-get update && sudo apt-get install -y vault

# 5. O'rnatilganini tekshirish
vault version
```

---

### 2-Qadam: Konfiguratsiya Faylini Yozish (`vault.hcl`)

Fayl yo'li: `/etc/vault.d/vault.hcl`

```bash
sudo tee /etc/vault.d/vault.hcl > /dev/null << 'EOF'
# Ma'lumotlarni saqlash mexanizmi (Integrated Raft Storage)
storage "raft" {
  path    = "/opt/vault/data"
  node_id = "node-1"
}

# Tarmoq tinglovchisi (TCP Listener)
listener "tcp" {
  address         = "0.0.0.0:8200"
  cluster_address = "0.0.0.0:8201"
  tls_disable     = 1  # Dastlabki sinov uchun TLS o'chiq (Day 5 da to'liq TLS/mTLS yoqiladi)
}

# Tashqi kirish manzillari
api_addr     = "http://192.168.0.250:8200"
cluster_addr = "http://192.168.0.250:8201"

# Web interfeysni yoqish
ui = true

# Linux RAM xotirani Swap'ga chiqarmaslik
disable_mlock = false
EOF
```

Ruxsatlar va papkalarni sozlash:
```bash
sudo mkdir -p /opt/vault/data
sudo chown -R vault:vault /opt/vault
sudo chown -R vault:vault /etc/vault.d
sudo chmod 640 /etc/vault.d/vault.hcl

# Vault binary fayliga RAM xotirani qulflash (mlock) huquqini berish
sudo setcap cap_ipc_lock=+ep $(readlink -f $(which vault))
```

---

### 3-Qadam: Systemd Xizmatini Yoqish

```bash
sudo systemctl daemon-reload
sudo systemctl enable vault
sudo systemctl restart vault
sudo systemctl status vault --no-pager
```

---

### 4-Qadam: Vault'ni Initsializatsiya qilish (Operator Init)

Endi Vault CLI bilan ishlash uchun muhit o'zgaruvchisini o'rnatamiz:

```bash
export VAULT_ADDR="http://127.0.0.1:8200"
vault status
```
> Holatda quyidagilar ko'rinadi:
> `Initialized   false`
> `Sealed        true`

**Initsializatsiya buyrug'i:**
```bash
vault operator init -key-shares=5 -key-threshold=3 > /home/doker/vault_keys.txt
chmod 600 /home/doker/vault_keys.txt
cat /home/doker/vault_keys.txt
```

⚠️ Chiqqan **5 ta Unseal Key** va **Initial Root Token**ni nusxalab oling!

---

### 5-Qadam: Unseal (Muhrdan chiqarish)

Threshold 3 qilib belgilangani sababli, kamida 3 ta alohida kalit kiritilishi shart:

```bash
# 1-kalit
vault operator unseal <UNSEAL_KEY_1>

# 2-kalit
vault operator unseal <UNSEAL_KEY_2>

# 3-kalit
vault operator unseal <UNSEAL_KEY_3>
```

3-kalit kiritilgach, quyidagi xabarni olasiz:
`Sealed false`

---

### 6-Qadam: Tizimga Kirish va Tekshirish

```bash
vault login <INITIAL_ROOT_TOKEN>
```
Muvaffaqiyatli kirilgach, statusni tekshiring:
```bash
vault token lookup
```

Endi brauzeringizdan oching:
👉 `http://192.168.0.250:8200/ui`

---

### 🎯 Day 1 Mini-Topshiriq:
1. Serverni qayta yuklang (`sudo reboot`) yoki `sudo systemctl restart vault` qiling.
2. `vault status` qilib, uning yana avtomatik `Sealed: true` holatiga qaytganini o'z ko'zingiz bilan ko'ring.
3. 3 ta unseal kalit bilan uni yana oching.
