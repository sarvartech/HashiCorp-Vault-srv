#!/bin/bash
# ==============================================================================
# HASHICORP VAULT ENTERPRISE - ALL-IN-ONE AUTOMATED INSTALLATION & CONFIGURATION
# Barcha paketlar, qaramliklar, konfiguratsiyalar, audit, firewall va CLI-Panel.
# ==============================================================================

set -e

# Ranglar
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "========================================================================"
echo "    🔐 HASHICORP VAULT ENTERPRISE - PRODUCTION AUTO-INSTALLER"
echo "    Universal o'rnatish, konfiguratsiya va CLI-Panel integratsiyasi"
echo "========================================================================"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}✖ Ushbu skriptni root huquqi bilan ishga tushiring: sudo bash $0${NC}"
  exit 1
fi

# Server IP aniqlash
# Server IP aniqlash
SERVER_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' || hostname -I | awk '{print $1}')
[ -z "$SERVER_IP" ] && SERVER_IP="127.0.0.1"

# Domain va Reverse Proxy
VAULT_DOMAIN="${VAULT_DOMAIN:-https://vault-srv.trustbank.uz}"
PROXY_CIDRS="${PROXY_CIDRS:-127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16}"

echo -e "${YELLOW}▶ 1. TIZIM VA DEPENDENCY PAKETLARNI O'RNATISH...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl wget gpg lsb-release jq ufw python3 python3-pip python3-requests

echo -e "${YELLOW}▶ 2. HASHICORP RASMIY REPOZITORIYSINI QO'SHISH...${NC}"
if ! command -v vault &> /dev/null; then
    wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg --yes
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list
    apt-get update -y
    apt-get install -y vault
else
    echo -e "${GREEN}✔ HashiCorp Vault allaqachon o'rnatilgan.$(vault version)${NC}"
fi

echo -e "${YELLOW}▶ 3. VAULT SERVISI VA KONFIGURATSIYANI SOZLASH (/etc/vault.d/vault.hcl)...${NC}"
mkdir -p /opt/vault/data /var/log/vault /var/backups/vault
chown -R vault:vault /opt/vault /var/log/vault
chmod 750 /var/log/vault

cat <<EOF > /etc/vault.d/vault.hcl
ui = true
disable_mlock = true

storage "file" {
  path = "/opt/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
  x_forwarded_for_authorized_addrs = "${PROXY_CIDRS}"
  x_forwarded_for_hop_skips = 0
}

api_addr = "${VAULT_DOMAIN}"
cluster_addr = "http://${SERVER_IP}:8201"
EOF

chown -R vault:vault /etc/vault.d
systemctl daemon-reload
systemctl enable vault
systemctl restart vault
sleep 2

echo -e "${YELLOW}▶ 4. ENVIRONMENT VA AUTO-UNSEAL SOZLASH...${NC}"
grep -qxF 'export VAULT_ADDR="http://127.0.0.1:8200"' /etc/environment || echo 'export VAULT_ADDR="http://127.0.0.1:8200"' >> /etc/environment
grep -qxF "export VAULT_PUBLIC_ADDR=\"${VAULT_DOMAIN}\"" /etc/environment || echo "export VAULT_PUBLIC_ADDR=\"${VAULT_DOMAIN}\"" >> /etc/environment
cat << EOF > /etc/profile.d/vault.sh
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_PUBLIC_ADDR="${VAULT_DOMAIN}"
if [ -f /etc/vault.d/vault_init.json ]; then
    export VAULT_TOKEN=\$(jq -r '.root_token' /etc/vault.d/vault_init.json 2>/dev/null)
fi
EOF
chmod +x /etc/profile.d/vault.sh
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_PUBLIC_ADDR="${VAULT_DOMAIN}"

echo -e "${YELLOW}▶ 5. INITIALIZATION & ROOT TOKEN SOZLASH...${NC}"
INIT_STATUS=$(vault status -format=json 2>/dev/null | jq -r '.initialized' || echo "false")

if [ "$INIT_STATUS" != "true" ]; then
    echo -e "${CYAN}Vault hali initsializatsiya qilinmagan. Yangi kalitlar yaratilmoqda...${NC}"
    vault operator init -key-shares=3 -key-threshold=2 -format=json > /etc/vault.d/vault_init.json
    chmod 600 /etc/vault.d/vault_init.json
    
    KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json)
    KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json)
    ROOT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json)
    
    vault operator unseal "$KEY1" > /dev/null
    vault operator unseal "$KEY2" > /dev/null
    export VAULT_TOKEN="$ROOT_TOKEN"
    echo -e "${GREEN}✔ Vault initsializatsiya qilindi va muhrdan ochildi!${NC}"
    echo -e "${YELLOW}Root Token: ${BOLD}$ROOT_TOKEN${NC}"
else
    echo -e "${GREEN}✔ Vault allaqachon initsializatsiya qilingan.${NC}"
    SEALED=$(vault status -format=json 2>/dev/null | jq -r '.sealed' || echo "false")
    if [ "$SEALED" == "true" ] && [ -f /etc/vault.d/vault_init.json ]; then
        KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json)
        KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json)
        vault operator unseal "$KEY1" > /dev/null 2>&1
        vault operator unseal "$KEY2" > /dev/null 2>&1
    fi
    
    if [ -z "$VAULT_TOKEN" ]; then
        if [ -f /etc/vault.d/vault_init.json ]; then
            VAULT_TOKEN=$(jq -r '.root_token' /etc/vault.d/vault_init.json)
        else
            echo -e "${CYAN}Mavjud Root / Admin Tokenni kiriting:${NC}"
            read -r -p "Root Token: " VAULT_TOKEN
        fi
    fi
    export VAULT_TOKEN
fi

# Auto-unseal xizmati
cat << 'EOF' > /usr/local/bin/vault-auto-unseal.sh
#!/bin/bash
export VAULT_ADDR="http://127.0.0.1:8200"
for i in {1..20}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8200/v1/sys/health || echo "000")
    if [ "$STATUS" == "200" ]; then exit 0; fi
    if [ "$STATUS" == "503" ]; then break; fi
    sleep 1
done
if [ -f /etc/vault.d/vault_init.json ]; then
    KEY1=$(jq -r '.unseal_keys_b64[0]' /etc/vault.d/vault_init.json)
    KEY2=$(jq -r '.unseal_keys_b64[1]' /etc/vault.d/vault_init.json)
    vault operator unseal "$KEY1" > /dev/null 2>&1
    vault operator unseal "$KEY2" > /dev/null 2>&1
fi
EOF
chmod +x /usr/local/bin/vault-auto-unseal.sh

cat << 'EOF' > /etc/systemd/system/vault-auto-unseal.service
[Unit]
Description=Auto Unseal HashiCorp Vault
After=vault.service
Wants=vault.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vault-auto-unseal.sh
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vault-auto-unseal.service

echo -e "${YELLOW}▶ 6. ENGINELAR VA AUDIT LOGNI YOQISH...${NC}"
vault secrets enable -path=secret kv-v2 > /dev/null 2>&1 || true
vault auth enable approle > /dev/null 2>&1 || true
vault auth enable userpass > /dev/null 2>&1 || true

touch /var/log/vault/vault_audit.log
chown vault:vault /var/log/vault/vault_audit.log
chmod 644 /var/log/vault/vault_audit.log
vault audit enable file file_path=/var/log/vault/vault_audit.log > /dev/null 2>&1 || true

echo -e "${YELLOW}▶ 7. XAVFSIZLIK FIREWALL (UFW) SOZLASH...${NC}"
ufw --force reset > /dev/null 2>&1 || true
ufw default deny incoming > /dev/null 2>&1 || true
ufw default allow outgoing > /dev/null 2>&1 || true
ufw allow 22/tcp comment 'SSH' > /dev/null 2>&1 || true
ufw allow 8200/tcp comment 'Vault UI and API' > /dev/null 2>&1 || true
ufw --force enable > /dev/null 2>&1 || true

echo -e "${YELLOW}▶ 8. CLI-PANELNI O'RNATISH (/usr/local/bin/vault-panel)...${NC}"
# Copy current python panel to /usr/local/bin/vault-panel.py
if [ -f "./vault_panel.py" ]; then
    cp ./vault_panel.py /usr/local/bin/vault-panel.py
elif [ -f "/tmp/vault_panel.py" ]; then
    cp /tmp/vault_panel.py /usr/local/bin/vault-panel.py
fi
chmod +x /usr/local/bin/vault-panel.py

cat << 'EOF' > /usr/local/bin/vault-panel
#!/bin/bash
exec python3 /usr/local/bin/vault-panel.py "$@"
EOF
chmod +x /usr/local/bin/vault-panel

echo ""
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}✔ BARCHA DEPENDENCY VA SOZLAMALAR MUVAFFAQIYATLI O'RNATILDI!${NC}"
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "  Vault Domain Web UI: ${CYAN}${VAULT_DOMAIN}/ui${NC}"
echo -e "  Direct Server Web UI: ${CYAN}http://${SERVER_IP}:8200/ui${NC}"
echo -e "  Vault API:           ${CYAN}http://127.0.0.1:8200${NC}"
echo -e "  Audit Log:           ${CYAN}/var/log/vault/vault_audit.log${NC}"
echo -e "  CLI-Panel:           ${YELLOW}vault-panel${NC} (istalgan joydan ishlaydi)"
echo -e "${GREEN}${BOLD}========================================================================${NC}"
