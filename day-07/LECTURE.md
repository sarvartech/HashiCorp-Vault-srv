# 📚 DAY 7: MA'RUZA MATNI
## 🔥 3 TA SERVERDA PRODUCTION RAFT HA KLASTER IMPLEMENTATION

---

### 1. Nega High Availability (HA) Va Nega Aynan 3 Ta Tugun?

Ishlab chiqarish (Production) muhitida Vault butun infratuzilmaning (barcha bazalar, backend servislar, CI/CD, Kubernetes) yuragi hisoblanadi. Agar bitta server o'chib qolsa, butun kompaniya ishi to'xtaydi. 

Shuning uchun Vault **Integrated Raft Storage** mexanizmi orqali yuqori bardoshli klaster (HA) sifatida quriladi.

#### ⚖️ Toq Sonlar Qoidasi va Quorum Formulari:
Raft algoritmi qaror qabul qilish (Leader saylash va yozuvlarni tasdiqlash) uchun **Quorum (Ko'pchilik ovozi)** talab qiladi:

$$\text{Quorum} = \left\lfloor \frac{N}{2} \right\rfloor + 1$$

| Tugunlar soni ($N$) | Quorum (Minimal tirik tugun) | Nechta server qulashiga bardosh beradi? |
| :---: | :---: | :---: |
| **1 ta** | 1 ta | 0 ta (SPOF - Single Point of Failure) |
| **2 ta** | 2 ta | 0 ta! (1 tasi o'chsa, klaster butunlay muzlaydi) |
| **3 ta (Tavsiya)** | **2 ta** | **1 ta server qulashiga bardosh beradi** |
| **5 ta (Enterprise)** | **3 ta** | **2 ta server qulashiga bardosh beradi** |

> [!WARNING]
> **Hech qachon 2 ta serverli HA qilmang!** 2 ta tugun bo'lsa, bittasi o'chishi bilan Quorum ($2/2 + 1 = 2$) yo'qoladi va klaster o'z-o'zini bloklab qo'yadi (Split-Brain himoyasi tufayli).

---

### 2. Klaster Arxitekturasi va Rollar

```
                        ┌──────────────────────────────────────────┐
                        │   Load Balancer (Nginx / HAProxy / F5)   │
                        │        https://vault.company.uz          │
                        └─────────────────────┬────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │ (Active: HTTP 200)      │ (Standby: HTTP 429)     │ (Standby: HTTP 429)
                    ▼                         ▼                         ▼
         ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
         │     NODE 1          │   │     NODE 2          │   │     NODE 3          │
         │   192.168.10.11     │   │   192.168.10.12     │   │   192.168.10.13     │
         │   👑 ACTIVE LEADER  │   │   🛡️ STANDBY        │   │   🛡️ STANDBY        │
         └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                    │                         │                         │
                    └─────────── Raft Cluster Port :8201 ───────────────┘
                                 (Log Replication & Heartbeat)
```

1. **Active Leader (1 ta):**
   * Barcha o'qish va yozish so'rovlarini bevosita qabul qiladi.
   * Ma'lumotlarni o'zining diskiga yozadi va Raft porti (`:8201`) orqali qolgan barcha Follower'larga tarqatadi (Replication Log).
   * Doimiy ravishda yurak urishi (Heartbeat) signalini yuborib turadi.

2. **Standby (Follower) Tugunlar (2 ta):**
   * Leader'dan ma'lumotlarni qabul qilib, o'z diskida nusxasini sinxronlashtirib boradi.
   * Agar tashqi mijoz Standby tugunga murojaat qilsa, Standby so'rovni avtomatik ravishda Leader'ga yo'naltiradi (Request Forwarding) yoki Load Balancer uni Leader'ga yuboradi.

3. **Saylov va Failover (1-2 soniyalik o'tish):**
   * Agar Node 1 to'satdan o'chib qolsa (reboot, hardware qulash, kabel uzilishi), Node 2 va Node 3 Heartbeat kelmay qolganini sezadi.
   * Bir necha millisoniyada yangi saylov (Election) boshlanadi.
   * Node 2 yoki Node 3 ko'pchilik ovozini (2 ta ovoz) olib, o'zini yangi **Active Leader** deb e'lon qiladi! Tizim 1-2 soniya ichida o'zini to'liq tiklaydi.

---

### 3. Tarmoq Portlari va Muloqot Zanjiri

Har bir Vault tuguni 2 ta alohida portda tinglaydi:

| Port | Nomi | Vazifasi | Kimlar ulanadi? |
| :--- | :--- | :--- | :--- |
| **8200** | **API / Listener Port** | HTTP/HTTPS API, Web UI, CLI buyruqlar | Mijozlar, Dasturlar, Nginx |
| **8201** | **Cluster Port** | Tugunlararo Raft log replikatsiyasi, Heartbeat, Shifrlangan muloqot | Faqat Vault serverlarning o'zi |

---

### 4. Nginx Load Balancer va Sog'liqni Tekshirish (`/v1/sys/health`)

Load Balancer qaysi tugun Active ekanligini qanday biladi?
Vault'da maxsus `/v1/sys/health` REST endpoint mavjud:

* **HTTP 200 OK** $\rightarrow$ Tugun hozir **Active Leader** (Trafikni shu yerga yuborish kerak).
* **HTTP 429 Too Many Requests** $\rightarrow$ Tugun tirik, lekin hozir **Standby** holatda.
* **HTTP 501 / 503** $\rightarrow$ Tugun Unseal qilinmagan yoki Nosoz.

Nginx yoki HAProxy orqali ushbu status kodlarni tekshirish orqali foydalanuvchi trafigi 100% har doim faol Leader'ga uzluksiz borib turishi ta'minlanadi!
