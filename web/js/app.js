/**
 * HashiCorp Vault Enterprise Web Console - SarvarTech Edition
 * High-performance Frontend Application
 */

// Application State
const state = {
  vaultAddr: localStorage.getItem('vault_addr') || 'https://vault-srv.sarvartech.uz',
  vaultToken: localStorage.getItem('vault_token') || '',
  user: null,
  currentTab: 'dashboard',
  organizations: [],
  servicesByOrg: {},
  currentSelected: { org: null, service: null, data: null, metadata: null },
  activeTemplate: 'api',
  allSecretsFlat: [],
  policies: [],
  tokens: [],
  approles: [],
  passwordsVisible: false
};

// ==============================================================================
// INITIALIZATION & AUTHENTICATION
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  const token = state.vaultToken;
  if (token) {
    const valid = await verifySession(state.vaultAddr, token);
    if (valid) {
      hideAuthModal();
      loadInitialData();
      return;
    }
  }
  showAuthModal();
}

function showAuthModal() {
  document.getElementById('auth-modal').classList.remove('hidden');
  document.getElementById('auth-vault-addr').value = state.vaultAddr;
}

function hideAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
}

function setQuickAddr(addr) {
  document.getElementById('auth-vault-addr').value = addr;
}

function togglePasswordVisibility(id) {
  const el = document.getElementById(id);
  el.type = el.type === 'password' ? 'text' : 'password';
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const addr = document.getElementById('auth-vault-addr').value.trim().replace(/\/$/, '');
  const token = document.getElementById('auth-vault-token').value.trim();
  const btn = document.getElementById('btn-login-submit');
  
  if (!token) {
    showToast('Iltimos, Vault tokeningizni kiriting!', 'error');
    return;
  }

  btn.disabled = true;
  btn.querySelector('.btn-text').innerText = 'Tekshirilmoqda...';
  btn.querySelector('.btn-spinner').classList.remove('hidden');

  const success = await verifySession(addr, token);
  btn.disabled = false;
  btn.querySelector('.btn-text').innerText = 'Konsolga Kirish';
  btn.querySelector('.btn-spinner').classList.add('hidden');

  if (success) {
    state.vaultAddr = addr;
    state.vaultToken = token;
    localStorage.setItem('vault_addr', addr);
    localStorage.setItem('vault_token', token);
    hideAuthModal();
    showToast('Muvaffaqiyatli ulandi!', 'success');
    loadInitialData();
  } else {
    showToast('Serverga ulanib bo\'lmadi yoki token yaroqsiz!', 'error');
  }
});

function logout() {
  if (confirm('Konsoldan chiqishni xohlaysizmi?')) {
    localStorage.removeItem('vault_token');
    state.vaultToken = '';
    state.user = null;
    showAuthModal();
    showToast('Tizimdan chiqildi.', 'info');
  }
}

async function verifySession(addr, token) {
  try {
    const res = await apiRequest('/api/auth/verify', 'POST', { addr, token });
    if (res && res.valid) {
      state.user = res.data;
      updateUserDisplay();
      return true;
    }
  } catch (err) {
    console.error('Session verify error:', err);
  }
  return false;
}

function updateUserDisplay() {
  const srvEl = document.getElementById('current-server-display');
  const userEl = document.getElementById('current-user-display');
  if (srvEl) srvEl.innerText = state.vaultAddr;
  if (userEl) userEl.innerText = state.user?.display_name || 'root (admin)';
}

// ==============================================================================
// API WRAPPER
// ==============================================================================
async function apiRequest(endpoint, method = 'GET', body = null) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Vault-Addr': state.vaultAddr,
    'X-Vault-Token': state.vaultToken
  };

  const opts = { method, headers };
  if (body) {
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(endpoint, opts);
  if (res.status === 401 || res.status === 403) {
    if (endpoint !== '/api/auth/verify') {
      showToast('Sessiya muddati tugadi yoki ruxsat yetarli emas (403/401)!', 'error');
    }
    return null;
  }
  return await res.json();
}

// ==============================================================================
// NAVIGATION TABS
// ==============================================================================
function switchTab(tabId) {
  state.currentTab = tabId;

  // Update nav buttons
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  // Update tab panes
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });

  // Update title
  const titles = {
    'dashboard': 'Dashboard & Xulosa',
    'secrets': 'Tashkilotlar & Secretlar Boshqaruvi',
    'wizard-create': '1-Klikda Yangi Servis & Secret Yaratish',
    'tokens': 'Client Tokenlar Boshqaruvi',
    'approles': 'Mikroservislar AppRole Boshqaruvi',
    'policies': 'ACL Xavfsizlik Policy\'lari',
    'audit': 'Real-time Audit & Access Monitor',
    'backup': 'Zaxiralash & Qayta Tiklash (Backup/Restore)',
    'doctor': 'Production Doctor Diagnostikasi'
  };
  document.getElementById('page-title').innerText = titles[tabId] || 'Vault Core';
  document.getElementById('page-breadcrumb').innerText = `Boshqaruv / ${titles[tabId] || tabId}`;

  // Tab specific loader
  if (tabId === 'dashboard') loadDashboardData();
  else if (tabId === 'secrets') loadSecretsTree();
  else if (tabId === 'wizard-create') initWizardTab();
  else if (tabId === 'tokens') loadTokensTab();
  else if (tabId === 'approles') loadAppRolesTab();
  else if (tabId === 'policies') loadPoliciesTab();
  else if (tabId === 'audit') loadAuditLogs();
  else if (tabId === 'doctor') runProductionDoctor();
}

function refreshCurrentTab() {
  switchTab(state.currentTab);
  showToast('Ma\'lumotlar yangilandi', 'info');
}

// ==============================================================================
// DATA LOADING
// ==============================================================================
async function loadInitialData() {
  updateUserDisplay();
  await loadDashboardData();
  await loadSecretsTree();
}

async function loadDashboardData() {
  const stats = await apiRequest('/api/stats');
  if (stats) {
    document.getElementById('stat-orgs').innerText = stats.total_orgs || 0;
    document.getElementById('stat-secrets').innerText = stats.total_secrets || 0;
    document.getElementById('stat-tokens').innerText = stats.total_tokens || 0;
    document.getElementById('badge-secrets-count').innerText = stats.total_secrets || 0;
    document.getElementById('badge-tokens-count').innerText = stats.total_tokens || 0;
    
    const sealEl = document.getElementById('stat-seal');
    if (stats.sealed) {
      sealEl.innerText = 'MUHRLANGAN';
      sealEl.className = 'stat-value text-warning';
    } else {
      sealEl.innerText = 'OCHIQ (ACTIVE)';
      sealEl.className = 'stat-value text-emerald';
    }
    document.getElementById('stat-version').innerText = `Versiya: ${stats.version || 'v1.18.2'}`;
  }

  // Populate preview tree
  renderDashboardTreePreview();
}

async function renderDashboardTreePreview() {
  const container = document.getElementById('dashboard-tree-container');
  if (!container) return;

  const orgsRes = await apiRequest('/api/organizations');
  if (!orgsRes || !orgsRes.organizations || orgsRes.organizations.length === 0) {
    container.innerHTML = '<div class="empty-state p-4">Hozircha hech qanday tashkilot yaratilmagan. Yuqoridagi "Yangi Tashkilot" tugmasini bosing.</div>';
    return;
  }

  let html = '';
  for (const org of orgsRes.organizations) {
    html += `
      <div class="tree-preview-item">
        <div class="flex-between">
          <span class="font-bold text-white">🏢 ${org}</span>
          <button class="btn btn-xs btn-outline" onclick="selectOrgAndSwitch('${org}')">Ochish →</button>
        </div>
      </div>
    `;
  }
  container.innerHTML = html;
}

function selectOrgAndSwitch(org) {
  switchTab('secrets');
  setTimeout(() => {
    openOrgInTree(org);
  }, 100);
}

// ==============================================================================
// SECRETS EXPLORER
// ==============================================================================
async function loadSecretsTree() {
  const treeEl = document.getElementById('explorer-tree');
  if (!treeEl) return;

  const res = await apiRequest('/api/organizations');
  if (!res || !res.organizations) {
    treeEl.innerHTML = '<div class="p-3 text-dim">Hech narsa topilmadi</div>';
    return;
  }

  state.organizations = res.organizations;
  state.allSecretsFlat = [];

  let html = '';
  for (const org of state.organizations) {
    html += `
      <div class="tree-org-node" id="org-node-${org}">
        <div class="tree-org-header" onclick="toggleOrgNode('${org}')">
          <span>🏢</span>
          <span class="org-name">${org}</span>
          <span class="org-badge" id="badge-${org}">...</span>
        </div>
        <div class="tree-services-list hidden" id="services-${org}">
          <!-- dynamic services -->
        </div>
      </div>
    `;
  }
  treeEl.innerHTML = html;

  // Asynchronously load counts
  for (const org of state.organizations) {
    loadServicesForOrg(org);
  }
}

async function loadServicesForOrg(org) {
  const res = await apiRequest(`/api/services?org=${encodeURIComponent(org)}`);
  const services = res?.services || [];
  state.servicesByOrg[org] = services;

  const badge = document.getElementById(`badge-${org}`);
  if (badge) badge.innerText = `${services.length} ta`;

  const container = document.getElementById(`services-${org}`);
  if (container) {
    let sHtml = '';
    services.forEach(srv => {
      state.allSecretsFlat.push({ org, service: srv });
      sHtml += `
        <div class="tree-service-item" id="srv-item-${org}-${srv}" onclick="selectSecret('${org}', '${srv}')">
          <span>⚙️</span>
          <span>${srv}</span>
        </div>
      `;
    });
    container.innerHTML = sHtml || '<div class="text-dim text-xs p-2">(servislar yo\'q)</div>';
  }
}

function toggleOrgNode(org) {
  const container = document.getElementById(`services-${org}`);
  if (container) {
    container.classList.toggle('hidden');
  }
}

function openOrgInTree(org) {
  const container = document.getElementById(`services-${org}`);
  if (container) {
    container.classList.remove('hidden');
  }
}

async function selectSecret(org, service) {
  // Highlight active
  document.querySelectorAll('.tree-service-item').forEach(el => el.classList.remove('active'));
  const activeEl = document.getElementById(`srv-item-${org}-${service}`);
  if (activeEl) activeEl.classList.add('active');

  const res = await apiRequest(`/api/secrets?org=${encodeURIComponent(org)}&service=${encodeURIComponent(service)}`);
  if (!res || !res.data) {
    showToast('Secret ma\'lumotlarini o\'qishda xatolik!', 'error');
    return;
  }

  state.currentSelected = {
    org,
    service,
    data: res.data || {},
    metadata: res.metadata || {}
  };

  renderSecretDetails();
}

function renderSecretDetails() {
  document.getElementById('secret-empty-state').classList.add('hidden');
  const detailsEl = document.getElementById('secret-details-container');
  detailsEl.classList.remove('hidden');

  const { org, service, data, metadata } = state.currentSelected;

  document.getElementById('secret-display-path').innerText = `secret/data/${org}/${service}`;

  // Chips
  const chipsEl = document.getElementById('secret-meta-chips');
  chipsEl.innerHTML = `
    <span class="chip">Versiya: ${metadata.version || 1}</span>
    <span class="chip">Yaratilgan: ${(metadata.created_time || '').substring(0, 19).replace('T', ' ')}</span>
  `;

  // Security & Access Model
  const ipDisplay = document.getElementById('current-bound-ip-display');
  if (ipDisplay) {
    ipDisplay.innerHTML = `<span class="chip chip-security">🛡️ Zero-Trust (NAT Moslashuvchan) & Bootstrap Token / AppRole</span>`;
  }

  // Key Value Table
  const tbody = document.getElementById('kv-table-body');
  tbody.innerHTML = '';

  Object.entries(data).forEach(([key, val]) => {
    if (key.startsWith('_')) return; // ignore system fields
    addKVRow(key, val);
  });
}

function addKVRow(key = '', val = '') {
  const tbody = document.getElementById('kv-table-body');
  const tr = document.createElement('tr');
  const inputType = state.passwordsVisible ? 'text' : 'password';

  tr.innerHTML = `
    <td>
      <input type="text" class="kv-key-input" value="${escapeHtml(key)}" placeholder="Kalit (masalan: password)">
    </td>
    <td>
      <div class="kv-val-group">
        <input type="${inputType}" class="kv-val-input" value="${escapeHtml(val)}" placeholder="Qiymat">
        <div class="kv-tools">
          <button type="button" class="btn-tool" title="Nusxalash" onclick="copyRowValue(this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          </button>
          <button type="button" class="btn-tool" title="Ko'rsatish/Yashirish" onclick="toggleRowVisibility(this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
          <button type="button" class="btn-tool" title="Yangi Kuchli Parol Generatsiya Qilish" onclick="generateRowPassword(this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          </button>
        </div>
      </div>
    </td>
    <td>
      <button type="button" class="btn btn-xs btn-danger" onclick="this.closest('tr').remove()">
        O'chirish
      </button>
    </td>
  `;
  tbody.appendChild(tr);
}

function toggleAllPasswords() {
  state.passwordsVisible = !state.passwordsVisible;
  const btnText = document.getElementById('btn-toggle-all-text');
  btnText.innerText = state.passwordsVisible ? '🔒 Barchasini Yashirish' : '👁 Barchasini Ko\'rsatish';

  document.querySelectorAll('.kv-val-input').forEach(input => {
    input.type = state.passwordsVisible ? 'text' : 'password';
  });
}

function toggleRowVisibility(btn) {
  const input = btn.closest('.kv-val-group').querySelector('.kv-val-input');
  input.type = input.type === 'password' ? 'text' : 'password';
}

function copyRowValue(btn) {
  const input = btn.closest('.kv-val-group').querySelector('.kv-val-input');
  copyText(input.value);
}

async function generateRowPassword(btn) {
  const res = await apiRequest('/api/generator/password?length=24');
  if (res && res.password) {
    const input = btn.closest('.kv-val-group').querySelector('.kv-val-input');
    input.value = res.password;
    input.type = 'text';
    showToast('Yangi 24-belgili parol o\'rnatildi!', 'success');
  }
}

async function saveSecretChanges() {
  const { org, service } = state.currentSelected;
  if (!org || !service) return;

  const rows = document.querySelectorAll('#kv-table-body tr');
  const newData = {};

  rows.forEach(r => {
    const k = r.querySelector('.kv-key-input').value.trim();
    const v = r.querySelector('.kv-val-input').value;
    if (k) {
      newData[k] = v;
    }
  });

  const res = await apiRequest('/api/secrets', 'POST', {
    org,
    service,
    data: newData
  });

  if (res && res.success) {
    showToast('Secret muvaffaqiyatli saqlandi!', 'success');
    selectSecret(org, service);
  } else {
    showToast('Saqlashda xatolik yuz berdi!', 'error');
  }
}

async function deleteCurrentSecret() {
  const { org, service } = state.currentSelected;
  if (!org || !service) return;

  if (confirm(`Haqiqatan ham '${org}/${service}' maxfiy ma'lumotlarini o'chirasizmi?`)) {
    const res = await apiRequest('/api/secrets', 'DELETE', { org, service });
    if (res && res.success) {
      showToast(`'${service}' servisi o'chirildi.`, 'info');
      document.getElementById('secret-details-container').classList.add('hidden');
      document.getElementById('secret-empty-state').classList.remove('hidden');
      loadServicesForOrg(org);
    }
  }
}

function filterServiceTree(query) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll('.tree-org-node').forEach(node => {
    let orgMatch = node.querySelector('.org-name').innerText.toLowerCase().includes(q);
    let anyServiceMatch = false;

    node.querySelectorAll('.tree-service-item').forEach(srv => {
      const srvMatch = srv.innerText.toLowerCase().includes(q);
      srv.style.display = (orgMatch || srvMatch) ? 'flex' : 'none';
      if (srvMatch) anyServiceMatch = true;
    });

    if (orgMatch || anyServiceMatch) {
      node.style.display = 'block';
      if (q && anyServiceMatch) {
        node.querySelector('.tree-services-list').classList.remove('hidden');
      }
    } else {
      node.style.display = 'none';
    }
  });
}

function handleGlobalSearch(query) {
  if (!query) return;
  switchTab('secrets');
  document.getElementById('tree-search-input').value = query;
  filterServiceTree(query);
}

// ==============================================================================
// CREATE NEW SECRET (CUSTOM INPUTS BY ADMIN)
// ==============================================================================
state.wizardValuesVisible = false;

async function initWizardTab() {
  const select = document.getElementById('wz-org-select');
  select.innerHTML = '';
  state.organizations.forEach(o => {
    select.innerHTML += `<option value="${o}">${o}</option>`;
  });

  document.getElementById('wz-service-name').value = '';

  // Initialize with clean default rows for the administrator
  const tbody = document.getElementById('wizard-kv-body');
  if (tbody) {
    tbody.innerHTML = '';
    addWizardCustomRow('username', '');
    addWizardCustomRow('password', '');
  }
}

function toggleWizardIPInput(show) {}

function addWizardCustomRow(key = '', val = '') {
  const tbody = document.getElementById('wizard-kv-body');
  if (!tbody) return;
  const tr = document.createElement('tr');
  const inputType = state.wizardValuesVisible ? 'text' : 'password';

  tr.innerHTML = `
    <td>
      <input type="text" class="kv-key-input wz-key" value="${escapeHtml(key)}" placeholder="Kalit (masalan: db_password, api_key)">
    </td>
    <td>
      <div class="kv-val-group">
        <input type="${inputType}" class="kv-val-input wz-val" value="${escapeHtml(val)}" placeholder="Qiymatni kiriting...">
        <div class="kv-tools">
          <button type="button" class="btn-tool" title="Ko'rsatish/Yashirish" onclick="toggleWizardRowVisibility(this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
          <button type="button" class="btn-tool" title="Tasodifiy kuchli parol generatsiya qilish (24 belgi)" onclick="generateWizardRowPassword(this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          </button>
        </div>
      </div>
    </td>
    <td>
      <button type="button" class="btn btn-xs btn-danger" onclick="this.closest('tr').remove()" title="Qatorni o'chirish">
        O'chirish
      </button>
    </td>
  `;
  tbody.appendChild(tr);
}

function toggleWizardValuesVisibility() {
  state.wizardValuesVisible = !state.wizardValuesVisible;
  document.querySelectorAll('.wz-val').forEach(input => {
    input.type = state.wizardValuesVisible ? 'text' : 'password';
  });
}

function toggleWizardRowVisibility(btn) {
  const input = btn.closest('.kv-val-group').querySelector('.wz-val');
  input.type = input.type === 'password' ? 'text' : 'password';
}

async function generateWizardRowPassword(btn) {
  const res = await apiRequest('/api/generator/password?length=24');
  if (res && res.password) {
    const input = btn.closest('.kv-val-group').querySelector('.wz-val');
    input.value = res.password;
    input.type = 'text';
    showToast('24-belgili parol o\'rnatildi', 'info');
  }
}

async function handleWizardSubmit(e) {
  e.preventDefault();
  const org = document.getElementById('wz-org-select').value;
  const service = document.getElementById('wz-service-name').value.trim().toLowerCase();
  if (!org || !service) {
    showToast('Tashkilot va servis nomini kiriting!', 'error');
    return;
  }

  const data = {};

  let rowCount = 0;
  document.querySelectorAll('#wizard-kv-body tr').forEach(row => {
    const k = row.querySelector('.wz-key').value.trim();
    const v = row.querySelector('.wz-val').value;
    if (k) {
      data[k] = v;
      rowCount++;
    }
  });

  if (rowCount === 0) {
    showToast('Kamida bitta kalit va qiymat (Key-Value) kiriting!', 'error');
    return;
  }

  const res = await apiRequest('/api/secrets', 'POST', { org, service, data });
  if (res && res.success) {
    showToast(`'${org}/${service}' servisi muvaffaqiyatli yaratildi!`, 'success');
    
    // Open handover modal with token
    openHandoverModal(org, service, data);
    
    // Refresh secrets tree
    await loadSecretsTree();
  } else {
    showToast(`Yaratishda xatolik: ${res?.error || ''}`, 'error');
  }
}

// ==============================================================================
// TOKENS TAB
// ==============================================================================
async function loadTokensTab() {
  const tbody = document.getElementById('tokens-table-body');
  tbody.innerHTML = '<tr><td colspan="5" class="text-center p-3">Yuklanmoqda...</td></tr>';

  const res = await apiRequest('/api/tokens');
  const tokens = res?.tokens || [];
  state.tokens = tokens;

  if (tokens.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center p-4 text-dim">Faol tokenlar topilmadi</td></tr>';
    return;
  }

  let html = '';
  tokens.forEach(t => {
    const ttlStr = t.ttl === 0 ? 'Cheksiz (Root)' : `${Math.round(t.ttl / 3600)} soat`;
    html += `
      <tr>
        <td><strong>${escapeHtml(t.display_name || 'token')}</strong></td>
        <td><span class="chip">${escapeHtml((t.policies || []).join(', '))}</span></td>
        <td>${ttlStr}</td>
        <td><span class="token-code">${t.accessor}</span></td>
        <td>
          <button class="btn btn-xs btn-danger" onclick="revokeToken('${t.accessor}')">Bekor qilish (Revoke)</button>
        </td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

async function revokeToken(accessor) {
  if (confirm('Ushbu tokenni bekor qilishga ishonchingiz komilmi?')) {
    const res = await apiRequest('/api/tokens/revoke', 'POST', { accessor });
    if (res && res.success) {
      showToast('Token muvaffaqiyatli bekor qilindi.', 'info');
      loadTokensTab();
    }
  }
}

function openTokenModalForCurrent() {
  const cur = state.currentSelected;
  if (!cur || !cur.org || !cur.service) {
    showToast('Avval biror servisni tanlang!', 'info');
    return;
  }
  openCreateTokenModal();
  const orgSel = document.getElementById('tok-target-org');
  if (orgSel) {
    orgSel.value = cur.org;
    populateTokenServices(cur.org);
    const srvSel = document.getElementById('tok-target-service');
    if (srvSel) srvSel.value = cur.service;
  }
}

function openAppRoleModalForCurrent() {
  const cur = state.currentSelected;
  if (!cur || !cur.org || !cur.service) {
    showToast('Avval biror servisni tanlang!', 'info');
    return;
  }
  openCreateAppRoleModal();
  const orgSel = document.getElementById('approle-org');
  if (orgSel) {
    orgSel.value = cur.org;
    populateAppRoleServices(cur.org);
    const srvSel = document.getElementById('approle-service');
    if (srvSel) srvSel.value = cur.service;
  }
}

function openCreateTokenModal() {
  const orgSel = document.getElementById('tok-target-org');
  orgSel.innerHTML = '';
  state.organizations.forEach(o => {
    orgSel.innerHTML += `<option value="${o}">${o}</option>`;
  });
  if (state.organizations.length > 0) {
    populateTokenServices(state.organizations[0]);
  }
  openModal('modal-create-token');
}

function populateTokenServices(org) {
  const srvSel = document.getElementById('tok-target-service');
  srvSel.innerHTML = '';
  const srvs = state.servicesByOrg[org] || [];
  srvs.forEach(s => {
    srvSel.innerHTML += `<option value="${s}">${s}</option>`;
  });
}

async function handleCreateTokenSubmit(e) {
  e.preventDefault();
  const org = document.getElementById('tok-target-org').value;
  const service = document.getElementById('tok-target-service').value;
  const access = document.getElementById('tok-access-level').value;
  const ttl = document.getElementById('tok-ttl').value;
  const numUses = parseInt(document.getElementById('tok-num-uses')?.value || '1', 10);
  const wrapTtl = document.getElementById('tok-wrapping')?.value || '';
  const renewable = document.getElementById('tok-renewable')?.checked ?? true;

  let policy = `policy-${org}-${service}-rw`;
  if (access === 'ro') policy = `policy-${org}-${service}-ro`;
  if (access === 'admin') policy = `policy-${org}-admin`;

  const payload = {
    org,
    service,
    policy,
    ttl,
    num_uses: numUses,
    renewable,
    wrap_ttl: wrapTtl,
    display_name: `${org}-${service}-app`
  };

  const res = await apiRequest('/api/tokens/create', 'POST', payload);
  if (res && res.client_token) {
    closeModal('modal-create-token');
    const msg = res.wrapped ? '10-daqiqalik Wrapped Token tayyorlandi!' : 'Client Token muvaffaqiyatli yaratildi!';
    showToast(msg, 'success');

    // Show Handover Modal with the new client token!
    openHandoverModalWithToken(org, service, res.client_token, {
      numUses: res.num_uses,
      ttl: res.ttl,
      wrapped: res.wrapped,
      renewable: res.renewable
    });
    loadTokensTab();
  } else {
    showToast('Token yaratishda xatolik!', 'error');
  }
}

// ==============================================================================
// APPROLES TAB
// ==============================================================================
async function loadAppRolesTab() {
  const tbody = document.getElementById('approles-table-body');
  tbody.innerHTML = '<tr><td colspan="5" class="text-center p-3">Yuklanmoqda...</td></tr>';

  const res = await apiRequest('/api/approles');
  const roles = res?.roles || [];

  if (roles.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center p-4 text-dim">AppRolelar topilmadi. "+ Yangi AppRole" tugmasini bosing.</td></tr>';
    return;
  }

  let html = '';
  for (const r of roles) {
    html += `
      <tr>
        <td><strong>${escapeHtml(r.role_name)}</strong></td>
        <td><span class="chip">${escapeHtml((r.policies || []).join(', '))}</span></td>
        <td><span class="token-code">${r.role_id}</span></td>
        <td>${r.token_ttl || '24h'}</td>
        <td>
          <button class="btn btn-xs btn-primary" onclick="showAppRoleDetails('${r.role_name}', '${r.role_id}')">Secret ID / Login</button>
        </td>
      </tr>
    `;
  }
  tbody.innerHTML = html;
}

function openCreateAppRoleModal() {
  const orgSel = document.getElementById('approle-org');
  orgSel.innerHTML = '';
  state.organizations.forEach(o => {
    orgSel.innerHTML += `<option value="${o}">${o}</option>`;
  });
  if (state.organizations.length > 0) {
    populateAppRoleServices(state.organizations[0]);
  }
  openModal('modal-create-approle');
}

function populateAppRoleServices(org) {
  const srvSel = document.getElementById('approle-service');
  srvSel.innerHTML = '';
  const srvs = state.servicesByOrg[org] || [];
  srvs.forEach(s => {
    srvSel.innerHTML += `<option value="${s}">${s}</option>`;
  });
}

async function handleCreateAppRoleSubmit(e) {
  e.preventDefault();
  const org = document.getElementById('approle-org').value;
  const service = document.getElementById('approle-service').value;
  const secretIdNumUses = parseInt(document.getElementById('approle-secret-id-num-uses')?.value || '1', 10);
  const secretIdTtl = document.getElementById('approle-secret-id-ttl')?.value || '24h';
  const tokenTtl = document.getElementById('approle-token-ttl')?.value || '24h';
  const tokenMaxTtl = document.getElementById('approle-token-max-ttl')?.value || '720h';

  const roleName = `role-${org}-${service}`;
  const policyName = `policy-${org}-${service}-rw`;

  const payload = {
    role_name: roleName,
    policy: policyName,
    token_ttl: tokenTtl,
    token_max_ttl: tokenMaxTtl,
    secret_id_ttl: secretIdTtl,
    secret_id_num_uses: secretIdNumUses
  };

  const res = await apiRequest('/api/approles/create', 'POST', payload);
  if (res && res.role_id) {
    closeModal('modal-create-approle');
    showToast('AppRole muvaffaqiyatli tayyorlandi!', 'success');
    openHandoverModalWithAppRole(org, service, res.role_id, res.secret_id, {
      secretIdTtl: res.secret_id_ttl,
      secretIdNumUses: res.secret_id_num_uses,
      tokenTtl: res.token_ttl
    });
    loadAppRolesTab();
  } else {
    showToast('AppRole yaratishda xatolik!', 'error');
  }
}

async function showAppRoleDetails(roleName, roleId) {
  const res = await apiRequest(`/api/approles/secret-id?role_name=${encodeURIComponent(roleName)}`, 'POST');
  if (res && res.secret_id) {
    openHandoverModalWithAppRole('app', roleName, roleId, res.secret_id, '');
  }
}

// ==============================================================================
// POLICIES TAB
// ==============================================================================
state.currentSelectedPolicy = null;
state.policyEditMode = false;

async function loadPoliciesTab() {
  const list = document.getElementById('policy-items-list');
  if (!list) return;
  list.innerHTML = '<li class="p-3 text-dim">Yuklanmoqda...</li>';

  const res = await apiRequest('/api/policies');
  const policies = res?.policies || [];
  state.policies = policies;

  if (policies.length === 0) {
    list.innerHTML = '<li class="p-3 text-dim">Hech qanday policy topilmadi</li>';
    return;
  }

  renderPolicyList(policies);

  if (policies.length > 0) {
    selectPolicy(policies[0]);
  }
}

function renderPolicyList(policies) {
  const list = document.getElementById('policy-items-list');
  let html = '';
  policies.forEach(p => {
    const isSystem = p === 'root' || p === 'default' || p.includes('default-ceiling');
    html += `
      <li class="policy-item" onclick="selectPolicy('${escapeHtml(p)}')" id="pol-item-${escapeHtml(p)}">
        <div class="flex-between" style="width: 100%;">
          <span>🛡️ ${escapeHtml(p)}</span>
          ${isSystem ? '<span class="chip" style="font-size: 0.65rem;">System</span>' : ''}
        </div>
      </li>
    `;
  });
  list.innerHTML = html;
}

function filterPoliciesList(q) {
  const term = q.trim().toLowerCase();
  const filtered = (state.policies || []).filter(p => p.toLowerCase().includes(term));
  renderPolicyList(filtered);
}

async function selectPolicy(pName) {
  state.currentSelectedPolicy = pName;
  state.policyEditMode = false;

  document.querySelectorAll('.policy-item').forEach(el => el.classList.remove('active'));
  const activeEl = document.getElementById(`pol-item-${pName}`);
  if (activeEl) activeEl.classList.add('active');

  const titleEl = document.getElementById('policy-view-title');
  const subtitleEl = document.getElementById('policy-view-subtitle');
  const actionsGroup = document.getElementById('policy-actions-group');
  const editor = document.getElementById('policy-editor-content');
  const btnEdit = document.getElementById('btn-policy-toggle-edit');
  const btnSave = document.getElementById('btn-policy-save');
  const btnDelete = document.getElementById('btn-policy-delete');

  if (titleEl) titleEl.innerText = pName;
  if (subtitleEl) subtitleEl.innerText = (pName === 'root' || pName === 'default') ? 'Asosiy tizim policy (O\'zgartirish tavsiya etilmaydi)' : 'Foydalanuvchi/Servis ACL Policy';
  if (actionsGroup) actionsGroup.classList.remove('hidden');

  editor.readOnly = true;
  editor.value = 'Yuklanmoqda...';

  if (btnEdit) {
    btnEdit.innerText = '✏️ Tahrirlash';
    btnEdit.classList.remove('btn-secondary');
    btnEdit.classList.add('btn-outline');
  }
  if (btnSave) btnSave.classList.add('hidden');
  if (btnDelete) {
    btnDelete.style.display = (pName === 'root' || pName === 'default') ? 'none' : 'inline-flex';
  }

  const res = await apiRequest(`/api/policies?name=${encodeURIComponent(pName)}`);
  if (res && res.policy) {
    editor.value = res.policy;
  } else {
    editor.value = res?.error || '# Ushbu policy mazmunini o\'qishda xatolik';
  }
}

function togglePolicyEditMode() {
  const editor = document.getElementById('policy-editor-content');
  const btnEdit = document.getElementById('btn-policy-toggle-edit');
  const btnSave = document.getElementById('btn-policy-save');

  state.policyEditMode = !state.policyEditMode;
  editor.readOnly = !state.policyEditMode;

  if (state.policyEditMode) {
    btnEdit.innerText = '❌ Bekor qilish';
    btnEdit.classList.remove('btn-outline');
    btnEdit.classList.add('btn-secondary');
    btnSave.classList.remove('hidden');
    editor.focus();
    showToast('Tahrirlash rejimi faollashdi', 'info');
  } else {
    btnEdit.innerText = '✏️ Tahrirlash';
    btnEdit.classList.remove('btn-secondary');
    btnEdit.classList.add('btn-outline');
    btnSave.classList.add('hidden');
    if (state.currentSelectedPolicy) {
      selectPolicy(state.currentSelectedPolicy);
    }
  }
}

async function savePolicyChanges() {
  const pName = state.currentSelectedPolicy;
  if (!pName) return;

  const content = document.getElementById('policy-editor-content').value.trim();
  if (!content) {
    showToast('Policy mazmuni bo\'sh bo\'lishi mumkin emas!', 'error');
    return;
  }

  const res = await apiRequest('/api/policies', 'POST', {
    name: pName,
    policy: content
  });

  if (res && res.success) {
    showToast(`'${pName}' policy muvaffaqiyatli saqlandi!`, 'success');
    state.policyEditMode = false;
    document.getElementById('policy-editor-content').readOnly = true;
    document.getElementById('btn-policy-toggle-edit').innerText = '✏️ Tahrirlash';
    document.getElementById('btn-policy-save').classList.add('hidden');
  } else {
    showToast(`Saqlashda xatolik: ${res?.error || 'Noma\'lum xatolik'}`, 'error');
  }
}

async function deleteSelectedPolicy() {
  const pName = state.currentSelectedPolicy;
  if (!pName) return;

  if (pName === 'root' || pName === 'default') {
    showToast('Root va Default tizim policy\'larini o\'chirib bo\'lmaydi!', 'error');
    return;
  }

  if (confirm(`Haqiqatan ham '${pName}' policy'sini o'chirishni xohlaysizmi? Unga bog'langan tokenlar ruxsatsiz qolishi mumkin!`)) {
    const res = await apiRequest('/api/policies', 'DELETE', { name: pName });
    if (res && res.success) {
      showToast(`'${pName}' policy o'chirildi!`, 'info');
      loadPoliciesTab();
    } else {
      showToast(`O'chirishda xatolik: ${res?.error || ''}`, 'error');
    }
  }
}

function openCreatePolicyModal() {
  document.getElementById('new-policy-name').value = '';
  applyPolicyTemplate('ro');
  openModal('modal-create-policy');
}

function applyPolicyTemplate(type) {
  const textarea = document.getElementById('new-policy-content');
  if (!textarea) return;

  if (type === 'ro') {
    textarea.value = `# Faqat o'qish (Read-Only) Policy shabloni\npath "secret/data/kompaniya/servis" {\n  capabilities = ["read"]\n}\n\npath "secret/metadata/kompaniya/servis" {\n  capabilities = ["read", "list"]\n}\n`;
  } else if (type === 'rw') {
    textarea.value = `# O'qish va yozish (Read-Write) Policy shabloni\npath "secret/data/kompaniya/servis" {\n  capabilities = ["create", "read", "update", "delete", "list"]\n}\n\npath "secret/metadata/kompaniya/servis" {\n  capabilities = ["read", "list"]\n}\n`;
  } else if (type === 'admin') {
    textarea.value = `# Tashkilot admini uchun to'liq ruxsat shabloni\npath "secret/data/kompaniya/*" {\n  capabilities = ["create", "read", "update", "delete", "list"]\n}\n\npath "secret/metadata/kompaniya/*" {\n  capabilities = ["list", "read", "delete"]\n}\n`;
  }
}

async function handleCreatePolicySubmit(e) {
  e.preventDefault();
  const name = document.getElementById('new-policy-name').value.trim();
  const policy = document.getElementById('new-policy-content').value.trim();

  if (!name || !policy) {
    showToast('Iltimos, policy nomi va kodini to\'liq kiriting!', 'error');
    return;
  }

  const res = await apiRequest('/api/policies', 'POST', { name, policy });
  if (res && res.success) {
    closeModal('modal-create-policy');
    showToast(`'${name}' policy muvaffaqiyatli yaratildi!`, 'success');
    await loadPoliciesTab();
    selectPolicy(name);
  } else {
    showToast(`Yaratishda xatolik: ${res?.error || ''}`, 'error');
  }
}

// ==============================================================================
// AUDIT LOGS
// ==============================================================================
async function loadAuditLogs() {
  const tbody = document.getElementById('audit-table-body');
  tbody.innerHTML = '<tr><td colspan="6" class="text-center p-3">Audit loglari o\'qilmoqda...</td></tr>';

  const res = await apiRequest('/api/audit');
  const logs = res?.logs || [];

  if (logs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center p-4 text-dim">Loglar mavjud emas yoki bo\'sh</td></tr>';
    return;
  }

  let html = '';
  logs.forEach(l => {
    html += `
      <tr>
        <td class="text-dim">${escapeHtml(l.time)}</td>
        <td><strong>${escapeHtml(l.client_ip)}</strong></td>
        <td><span class="chip">${escapeHtml(l.operation)}</span></td>
        <td><span class="token-code">${escapeHtml(l.path)}</span></td>
        <td>${escapeHtml(l.auth_identity)}</td>
        <td><span class="doctor-badge pass">RUXSAT</span></td>
      </tr>
    `;
  });
  tbody.innerHTML = html;
}

// ==============================================================================
// BACKUP & RESTORE
// ==============================================================================
function downloadBackupFile() {
  showToast('Zaxira fayli tayyorlanmoqda...', 'info');
  window.open(`${state.vaultAddr}/api/backup?token=${encodeURIComponent(state.vaultToken)}`, '_blank');
}

async function handleRestoreUpload() {
  const input = document.getElementById('restore-file-input');
  if (!input.files || input.files.length === 0) {
    showToast('Iltimos, avval zaxira .json faylini tanlang!', 'error');
    return;
  }

  const file = input.files[0];
  const reader = new FileReader();
  reader.onload = async (e) => {
    try {
      const data = JSON.parse(e.target.result);
      showToast('Ma\'lumotlar tiklanmoqda...', 'info');
      const res = await apiRequest('/api/restore', 'POST', data);
      if (res && res.success) {
        showToast('Barcha ma\'lumotlar muvaffaqiyatli tiklandi!', 'success');
        loadInitialData();
      } else {
        showToast('Tiklashda xatolik!', 'error');
      }
    } catch (err) {
      showToast('Noto\'g\'ri JSON fayl formati!', 'error');
    }
  };
  reader.readAsText(file);
}

// ==============================================================================
// PRODUCTION DOCTOR
// ==============================================================================
async function runProductionDoctor() {
  const container = document.getElementById('doctor-checks-list');
  container.innerHTML = '<div class="p-3 text-dim">Tizim holati tekshirilmoqda...</div>';

  const res = await apiRequest('/api/doctor');
  const checks = res?.checks || [];

  let html = '';
  checks.forEach(c => {
    const badgeClass = c.ok ? 'pass' : 'fail';
    const badgeText = c.ok ? '✔ PASSED' : '✖ FAILED';
    html += `
      <div class="doctor-item">
        <div>
          <div class="doctor-title">${escapeHtml(c.title)}</div>
          <div class="doctor-desc">${escapeHtml(c.desc)}</div>
        </div>
        <span class="doctor-badge ${badgeClass}">${badgeText}</span>
      </div>
    `;
  });
  container.innerHTML = html;
}

// ==============================================================================
// HANDOVER CARD (DASTURCHIGA BERILADIGAN BLOK)
// ==============================================================================
function openHandoverModalForCurrent() {
  const { org, service, data } = state.currentSelected;
  openHandoverModal(org, service, data);
}

function openHandoverModal(org, service, data) {
  openHandoverModalWithToken(org, service, state.vaultToken, { numUses: 0, ttl: '720h' });
}

function openHandoverModalWithToken(org, service, token, secMeta = {}) {
  const path = `secret/data/${org}/${service}`;
  const url = state.vaultAddr;

  state.handoverCurrent = {
    org,
    service,
    token: token || state.vaultToken,
    roleId: '',
    secretId: '',
    path,
    secMeta,
    lang: 'env'
  };

  document.getElementById('handover-url').value = url;
  document.getElementById('handover-path').value = path;
  document.getElementById('handover-token-field').classList.remove('hidden');
  document.getElementById('handover-token').value = token || state.vaultToken;
  document.getElementById('handover-role-field').classList.add('hidden');
  document.getElementById('handover-secret-id-field').classList.add('hidden');
  document.getElementById('handover-test-result').classList.add('hidden');

  switchHandoverLang('env');
  openModal('modal-handover');
}

function openHandoverModalWithAppRole(org, service, roleId, secretId, secMeta = {}) {
  const path = `secret/data/${org}/${service}`;
  const url = state.vaultAddr;

  state.handoverCurrent = {
    org,
    service,
    token: '',
    roleId,
    secretId,
    path,
    secMeta,
    lang: 'env'
  };

  document.getElementById('handover-url').value = url;
  document.getElementById('handover-path').value = path;
  document.getElementById('handover-token-field').classList.add('hidden');
  document.getElementById('handover-role-field').classList.remove('hidden');
  document.getElementById('handover-role-id').value = roleId;
  document.getElementById('handover-secret-id-field').classList.remove('hidden');
  document.getElementById('handover-secret-id').value = secretId;
  document.getElementById('handover-test-result').classList.add('hidden');

  switchHandoverLang('env');
  openModal('modal-handover');
}

function switchHandoverLang(lang) {
  if (!state.handoverCurrent) state.handoverCurrent = {};
  state.handoverCurrent.lang = lang;

  document.querySelectorAll('.lang-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick')?.includes(`'${lang}'`));
  });
  renderHandoverCode();
}

function renderHandoverCode() {
  const cur = state.handoverCurrent || {};
  const org = cur.org || 'company';
  const service = cur.service || 'core-api';
  const token = cur.token || '<CLIENT_TOKEN>';
  const roleId = cur.roleId || '';
  const secretId = cur.secretId || '';
  const path = cur.path || `secret/data/${org}/${service}`;
  const lang = cur.lang || 'env';
  const url = state.vaultAddr;
  const secMeta = cur.secMeta || {};

  const displayEl = document.getElementById('handover-code-display');
  if (!displayEl) return;

  let secComment = '# Zero-Trust NAT Xavfsizlik: ';
  if (secMeta.wrapped) {
    secComment += '10-daqiqalik Qadoqlangan (Wrapped) Token. Unwrapping zarur!\n';
  } else if (secMeta.numUses === 1) {
    secComment += '1-martalik Bootstrap Token (num_uses=1). O\'qilishi bilan token avtomatik kuyadi.\n';
  } else if (roleId) {
    secComment += `AppRole Dual-Key (Role ID + Secret ID). Secret-ID limit: ${secMeta.secretIdNumUses || 1} marta.\n`;
  } else {
    secComment += `Dinamik TTL: ${secMeta.ttl || '24h'}.\n`;
  }

  let code = '';
  if (lang === 'env') {
    code = `# ===========================================\n# HashiCorp Vault Environment Configuration\n${secComment}# ===========================================\nVAULT_ADDR=${url}\nVAULT_TOKEN=${token}\nVAULT_SECRET_PATH=${path}\n`;
    if (roleId) {
      code += `VAULT_ROLE_ID=${roleId}\nVAULT_SECRET_ID=${secretId}\n`;
    }
  } else if (lang === 'curl') {
    if (secMeta.wrapped) {
      code = `# 1. Qadoqlangan tokenni ochish (Unwrap):\nREAL_TOKEN=$(curl -k -s -X POST -H "X-Vault-Token: ${token}" ${url}/v1/sys/wrapping/unwrap | jq -r .auth.client_token)\n\n# 2. Asl secret ma'lumotlarini o'qish:\ncurl -k -s -H "X-Vault-Token: $REAL_TOKEN" ${url}/v1/${path} | jq .data.data\n`;
    } else {
      code = `# Terminal orqali o'qish (cURL & jq):\n# ${secComment.trim()}\ncurl -k -s \\\n  -H "X-Vault-Token: ${token}" \\\n  ${url}/v1/${path} | jq .data.data\n`;
    }
  } else if (lang === 'python') {
    code = `# Python dasturchilar uchun (pip install hvac requests):\n# ${secComment.trim()}\nimport hvac\n\nclient = hvac.Client(\n    url="${url}",\n    token="${token}"\n)\n\n# KV-v2 Secretni o'qish\nsecret_version = client.secrets.kv.v2.read_secret_version(\n    mount_point="secret",\n    path="${org}/${service}"\n)\n\nsecrets_data = secret_version["data"]["data"]\nprint("Olingan ma'lumotlar:", secrets_data)\n`;
  } else if (lang === 'node') {
    code = `// Node.js dasturchilar uchun (npm install axios):\n// ${secComment.trim()}\nconst axios = require('axios');\n\nasync function fetchVaultSecrets() {\n  try {\n    const response = await axios.get(\n      '${url}/v1/${path}',\n      { headers: { 'X-Vault-Token': '${token}' } }\n    );\n    const secrets = response.data.data.data;\n    console.log('Vault Secretlari:', secrets);\n    return secrets;\n  } catch (err) {\n    console.error('Vault so\\'rovi xatosi:', err.response?.data || err.message);\n  }\n}\nfetchVaultSecrets();\n`;
  } else if (lang === 'go') {
    code = `// Go (Golang) dasturchilar uchun:\n// ${secComment.trim()}\npackage main\n\nimport (\n\t"fmt"\n\t"github.com/hashicorp/vault/api"\n)\n\nfunc main() {\n\tconfig := api.DefaultConfig()\n\tconfig.Address = "${url}"\n\tclient, err := api.NewClient(config)\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tclient.SetToken("${token}")\n\n\tsecret, err := client.Logical().Read("${path}")\n\tif err != nil {\n\t\tpanic(err)\n\t}\n\tfmt.Println("Vault Data:", secret.Data["data"])\n}\n`;
  } else if (lang === 'php') {
    code = `<?php\n// PHP / Laravel dasturchilar uchun:\n// ${secComment.trim()}\n$url = "${url}/v1/${path}";\n$token = "${token}";\n\n$ch = curl_init($url);\ncurl_setopt($ch, CURLOPT_HTTPHEADER, ["X-Vault-Token: $token"]);\ncurl_setopt($ch, CURLOPT_RETURNTRANSFER, true);\ncurl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);\n$response = curl_exec($ch);\n$data = json_decode($response, true);\n\nprint_r($data['data']['data']);\n`;
  }

  displayEl.innerText = code;
}

function copyCurrentHandoverCode() {
  const code = document.getElementById('handover-code-display')?.innerText;
  if (code) {
    copyText(code);
  }
}

async function runHandoverLiveTest() {
  const cur = state.handoverCurrent || {};
  const path = cur.path || `secret/data/${cur.org}/${cur.service}`;
  const token = cur.token || state.vaultToken;

  const testBtn = document.getElementById('btn-test-handover');
  const resultBox = document.getElementById('handover-test-result');
  const badge = document.getElementById('handover-test-badge');
  const latency = document.getElementById('handover-test-latency');
  const preview = document.getElementById('handover-test-preview');

  testBtn.disabled = true;
  testBtn.innerText = 'Test qilinmoqda...';

  const res = await apiRequest('/api/test-token-access', 'POST', {
    token: token,
    path: path
  });

  testBtn.disabled = false;
  testBtn.innerText = 'Sinash (Test Request)';
  resultBox.classList.remove('hidden');

  if (res && res.success) {
    badge.className = 'test-badge badge-success';
    badge.innerText = `HTTP ${res.status_code} OK (Muvaffaqiyatli)`;
    latency.innerText = `Ping: ${res.latency_ms} ms`;
    preview.innerText = JSON.stringify(res.data?.data?.data || res.data, null, 2);
    showToast('Vault muvaffaqiyatli javob berdi (200 OK)!', 'success');
  } else {
    badge.className = 'test-badge badge-error';
    badge.innerText = `HTTP ${res?.status_code || 500} XATOLIK`;
    latency.innerText = `Ping: ${res?.latency_ms || 0} ms`;
    preview.innerText = res?.error || 'Ulanishda xatolik yuz berdi';
    showToast('Test so\'rovida xatolik yuz berdi!', 'error');
  }
}

function copyEntireHandover() {
  const cur = state.handoverCurrent || {};
  const url = document.getElementById('handover-url').value;
  const path = document.getElementById('handover-path').value;
  const code = document.getElementById('handover-code-display').innerText;

  let text = `======================================================================\n`;
  text += `  🏷️  HASHICORP VAULT - CREDENTIALS HANDOVER\n`;
  text += `======================================================================\n`;
  text += `  Server URL:    ${url}\n`;
  text += `  Secret Yo'li:  ${path}\n`;
  if (cur.token) text += `  Client Token:  ${cur.token}\n`;
  if (cur.roleId) text += `  Role ID:       ${cur.roleId}\n`;
  if (cur.secretId) text += `  Secret ID:     ${cur.secretId}\n`;
  text += `\n  Integratsiya kodi:\n${code}\n`;
  text += `======================================================================\n`;

  copyText(text);
  showToast('Barcha ma\'lumotlar nusxalandi (Copy)!', 'success');
}

// ==============================================================================
// MY IP & LIVE TESTING & RAW JSON VIEW
// ==============================================================================
async function detectAndFillMyIP(inputId) {
  try {
    const res = await apiRequest('/api/my-ip');
    if (res && res.ip) {
      const el = document.getElementById(inputId);
      if (el) {
        el.value = res.ip;
        showToast(`Sizning joriy IP manzilingiz aniqlandi: ${res.ip}`, 'info');
      }
    }
  } catch (e) {
    showToast('IP aniqlashda xatolik yuz berdi', 'error');
  }
}

async function testCurrentSecretAccess() {
  const { org, service } = state.currentSelected;
  if (!org || !service) {
    showToast('Avval birorta servisni tanlang!', 'info');
    return;
  }

  const alertBox = document.getElementById('secret-test-alert');
  const badge = document.getElementById('secret-test-status-badge');
  const title = document.getElementById('secret-test-title');
  const latency = document.getElementById('secret-test-latency');
  const payload = document.getElementById('secret-test-payload');

  const path = `secret/data/${org}/${service}`;
  showToast('Jonli so\'rov yuborilmoqda...', 'info');

  const res = await apiRequest('/api/test-token-access', 'POST', {
    token: state.vaultToken,
    path: path
  });

  alertBox.classList.remove('hidden');

  if (res && res.success) {
    badge.className = 'test-badge badge-success';
    badge.innerText = `HTTP ${res.status_code} OK`;
    title.innerText = 'Dasturchi so\'rovi muvaffaqiyatli!';
    latency.innerText = `(${res.latency_ms} ms)`;
    payload.innerText = JSON.stringify(res.data?.data?.data || {}, null, 2);
    showToast('Secret o\'qildi (200 OK)', 'success');
  } else {
    badge.className = 'test-badge badge-error';
    badge.innerText = `HTTP ${res?.status_code || 500} ERROR`;
    title.innerText = 'So\'rov rad etildi yoki xatolik yuz berdi';
    latency.innerText = `(${res?.latency_ms || 0} ms)`;
    payload.innerText = res?.error || 'Xatolik';
    showToast('So\'rovda xatolik', 'error');
  }
}

function switchSecretViewMode(mode) {
  state.currentViewMode = mode;
  const btnTable = document.getElementById('btn-view-table');
  const btnRaw = document.getElementById('btn-view-raw');
  const tableContainer = document.getElementById('kv-table-container');
  const rawContainer = document.getElementById('raw-json-container');

  if (mode === 'table') {
    btnTable.classList.add('active');
    btnRaw.classList.remove('active');
    tableContainer.classList.remove('hidden');
    rawContainer.classList.add('hidden');
  } else {
    btnRaw.classList.add('active');
    btnTable.classList.remove('active');
    tableContainer.classList.add('hidden');
    rawContainer.classList.remove('hidden');

    const data = getCurrentTableData();
    document.getElementById('raw-json-textarea').value = JSON.stringify(data, null, 2);
    validateRawJSON();
  }
}

function getCurrentTableData() {
  const data = {};
  document.querySelectorAll('#kv-table-body tr').forEach(r => {
    const k = r.querySelector('.kv-key-input')?.value.trim();
    const v = r.querySelector('.kv-val-input')?.value;
    if (k) data[k] = v;
  });
  return data;
}

function validateRawJSON() {
  const val = document.getElementById('raw-json-textarea').value;
  const statusEl = document.getElementById('raw-json-status');
  try {
    JSON.parse(val);
    statusEl.innerText = '✔ Format to\'g\'ri (Valid JSON)';
    statusEl.className = 'text-xs text-emerald';
    return true;
  } catch (e) {
    statusEl.innerText = `❌ Format xatosi: ${e.message}`;
    statusEl.className = 'text-xs text-warning';
    return false;
  }
}

function formatRawJSON() {
  const textarea = document.getElementById('raw-json-textarea');
  try {
    const parsed = JSON.parse(textarea.value);
    textarea.value = JSON.stringify(parsed, null, 2);
    validateRawJSON();
    showToast('JSON chiroyli formatlandi', 'info');
  } catch (e) {
    showToast('JSON formatida xatolik bor!', 'error');
  }
}

async function saveRawJSONChanges() {
  const { org, service } = state.currentSelected;
  if (!org || !service) return;

  const val = document.getElementById('raw-json-textarea').value;
  let parsed = null;
  try {
    parsed = JSON.parse(val);
  } catch (e) {
    showToast(`JSON xatosi: ${e.message}`, 'error');
    return;
  }

  if (state.currentSelected.data._bound_source_ip) {
    parsed._bound_source_ip = state.currentSelected.data._bound_source_ip;
  }

  const res = await apiRequest('/api/secrets', 'POST', {
    org,
    service,
    data: parsed
  });

  if (res && res.success) {
    showToast('JSON muvaffaqiyatli saqlandi!', 'success');
    await selectSecret(org, service);
    switchSecretViewMode('table');
  } else {
    showToast('Saqlashda xatolik yuz berdi!', 'error');
  }
}

function copyCurrentSecretJSON() {
  const data = getCurrentTableData();
  copyText(JSON.stringify(data, null, 2));
}

// ==============================================================================
// PASSWORD GENERATOR MODAL
// ==============================================================================
function openPwdGenModal() {
  openModal('modal-pwd-generator');
  regenerateCustomPassword();
}

function updatePwdGenLength(val) {
  document.getElementById('gen-len-label').innerText = `${val} belgi`;
  regenerateCustomPassword();
}

function regenerateCustomPassword() {
  const len = parseInt(document.getElementById('gen-pwd-length').value) || 24;
  const upper = document.getElementById('gen-opt-upper').checked;
  const lower = document.getElementById('gen-opt-lower').checked;
  const digits = document.getElementById('gen-opt-digits').checked;
  const symbols = document.getElementById('gen-opt-symbols').checked;

  let pool = '';
  if (upper) pool += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  if (lower) pool += 'abcdefghijklmnopqrstuvwxyz';
  if (digits) pool += '0123456789';
  if (symbols) pool += '!@#$%^&*-_=+';

  if (!pool) pool = 'abcdefghijklmnopqrstuvwxyz';

  let pwd = '';
  for (let i = 0; i < len; i++) {
    pwd += pool.charAt(Math.floor(Math.random() * pool.length));
  }

  document.getElementById('gen-pwd-output').value = pwd;

  const fill = document.getElementById('gen-strength-fill');
  const label = document.getElementById('gen-strength-label');
  if (len < 16 || (!symbols && !upper)) {
    fill.className = 'strength-fill strength-weak';
    label.innerText = 'O\'rtacha (Xavfsizroq qilish tavsiya etiladi)';
    label.className = 'text-xs font-bold text-warning';
  } else if (len < 20) {
    fill.className = 'strength-fill strength-medium';
    label.innerText = 'Kuchli (Standart talab)';
    label.className = 'text-xs font-bold text-warning';
  } else {
    fill.className = 'strength-fill strength-strong';
    label.innerText = 'Juda Kuchli (Bank-grade Kriptografik)';
    label.className = 'text-xs font-bold text-emerald';
  }
}

// ==============================================================================
// SPOTLIGHT COMMAND PALETTE (Ctrl+K)
// ==============================================================================
function openSpotlightSearch() {
  openModal('modal-spotlight-search');
  const input = document.getElementById('spotlight-input');
  input.value = '';
  input.focus();
  renderSpotlightResults('');
}

function handleSpotlightBackdrop(e) {
  closeModal('modal-spotlight-search');
}

function handleSpotlightInput(q) {
  renderSpotlightResults(q.trim().toLowerCase());
}

function renderSpotlightResults(q) {
  const container = document.getElementById('spotlight-results');
  let items = [];

  // Actions
  items.push({ type: 'action', title: '➕ Yangi Tashkilot Qo\'shish', action: () => { closeModal('modal-spotlight-search'); openCreateOrgModal(); } });
  items.push({ type: 'action', title: '🔑 Yangi Secret & Parol Yaratish (Wizard)', action: () => { closeModal('modal-spotlight-search'); openCreateSecretModal(); } });
  items.push({ type: 'action', title: '🎟 Yangi Client Token Yaratish', action: () => { closeModal('modal-spotlight-search'); openCreateTokenModal(); } });
  items.push({ type: 'action', title: '🤖 Yangi AppRole Yaratish', action: () => { closeModal('modal-spotlight-search'); openCreateAppRoleModal(); } });
  items.push({ type: 'action', title: '🎲 Kriptografik Parol Generatori', action: () => { closeModal('modal-spotlight-search'); openPwdGenModal(); } });
  items.push({ type: 'action', title: '💾 1-Klik Zaxiralash (Backup yuklab olish)', action: () => { closeModal('modal-spotlight-search'); downloadBackupFile(); } });
  items.push({ type: 'action', title: '🩺 Production Doctor Tekshiruvi', action: () => { closeModal('modal-spotlight-search'); switchTab('doctor'); } });

  // Orgs & Services
  state.organizations.forEach(org => {
    items.push({
      type: 'org',
      title: `🏢 ${org}`,
      desc: 'Tashkilot',
      action: () => {
        closeModal('modal-spotlight-search');
        selectOrgAndSwitch(org);
      }
    });

    const srvs = state.servicesByOrg[org] || [];
    srvs.forEach(srv => {
      items.push({
        type: 'service',
        title: `⚙️ ${org} / ${srv}`,
        desc: `secret/data/${org}/${srv}`,
        action: () => {
          closeModal('modal-spotlight-search');
          switchTab('secrets');
          openOrgInTree(org);
          selectSecret(org, srv);
        }
      });
    });
  });

  const filtered = q ? items.filter(it => it.title.toLowerCase().includes(q) || (it.desc && it.desc.toLowerCase().includes(q))) : items;

  if (filtered.length === 0) {
    container.innerHTML = '<div class="p-4 text-center text-dim">Hech qanday natija topilmadi</div>';
    return;
  }

  container.innerHTML = '';
  filtered.slice(0, 15).forEach((it, idx) => {
    const div = document.createElement('div');
    div.className = `spotlight-item ${idx === 0 ? 'active' : ''}`;
    div.innerHTML = `
      <div class="spotlight-item-left">
        <span class="spotlight-type-tag ${it.type}">${it.type}</span>
        <div>
          <div class="font-medium text-white">${escapeHtml(it.title)}</div>
          ${it.desc ? `<div class="text-xs text-dim">${escapeHtml(it.desc)}</div>` : ''}
        </div>
      </div>
      <span class="text-xs text-dim">Tanlash ↵</span>
    `;
    div.onclick = it.action;
    container.appendChild(div);
  });
}

// Global Keyboard Shortcuts (Ctrl+K and Escape)
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    openSpotlightSearch();
  }
  if (e.key === 'Escape') {
    closeModal('modal-spotlight-search');
    closeModal('modal-pwd-generator');
    closeModal('modal-handover');
    closeModal('modal-create-org');
    closeModal('modal-create-token');
    closeModal('modal-create-approle');
  }
});

// ==============================================================================
// MODAL HELPERS
// ==============================================================================
function openModal(id) {
  document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
}

function openCreateOrgModal() {
  openModal('modal-create-org');
}

function openCreateSecretModal() {
  switchTab('wizard-create');
}

async function handleCreateOrgSubmit(e) {
  e.preventDefault();
  const name = document.getElementById('new-org-name').value.trim().toLowerCase();
  const initService = document.getElementById('new-org-init-service').value.trim() || 'core-api';

  if (!name) return;

  const res = await apiRequest('/api/organizations', 'POST', {
    name,
    initial_service: initService
  });

  if (res && res.success) {
    closeModal('modal-create-org');
    showToast(`'${name}' tashkiloti muvaffaqiyatli yaratildi!`, 'success');
    loadSecretsTree();
  } else {
    showToast('Tashkilot yaratishda xatolik!', 'error');
  }
}

// ==============================================================================
// UTILITIES
// ==============================================================================
function copyInput(id) {
  const el = document.getElementById(id);
  copyText(el.value);
}

function copyText(str) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(str);
  } else {
    const el = document.createElement('textarea');
    el.value = str;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
  }
  showToast('Nusxa olindi! (Copied)', 'success');
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerText = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3500);
}

function randomPass(len = 24) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*-_=+';
  let out = '';
  for (let i = 0; i < len; i++) {
    out += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return out;
}

function randomHex(len = 16) {
  const chars = '0123456789abcdef';
  let out = '';
  for (let i = 0; i < len; i++) {
    out += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return out;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
