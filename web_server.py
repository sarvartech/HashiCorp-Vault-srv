#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HashiCorp Vault Enterprise - Web Management Console Backend Server
Serves static UI files and provides high-performance REST API proxy to Vault.
"""

import os
import sys
import json
import time
import secrets
import string
import datetime
import subprocess
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PORT = 5000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
AUDIT_LOG_FILE = "/var/log/vault/vault_audit.log"

class VaultWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Vault-Token, X-Vault-Addr")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def parse_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 0:
                raw = self.rfile.read(length).decode("utf-8")
                return json.loads(raw)
        except Exception:
            pass
        return {}

    def get_vault_context(self):
        v_addr = self.headers.get("X-Vault-Addr", os.environ.get("VAULT_ADDR", "https://vault-srv.sarvartech.uz")).rstrip("/")
        v_token = self.headers.get("X-Vault-Token", os.environ.get("VAULT_TOKEN", ""))
        return v_addr, v_token

    def get_client_ip(self):
        client_ip = self.headers.get("X-Real-IP") or self.headers.get("X-Forwarded-For")
        if client_ip:
            return client_ip.split(",")[0].strip()
        return self.client_address[0]

    def send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if not path.startswith("/api/"):
            return super().do_GET()

        v_addr, v_token = self.get_vault_context()
        v_headers = {"X-Vault-Token": v_token, "Content-Type": "application/json"}

        # 1. Stats
        if path == "/api/stats":
            total_orgs = 0
            total_secrets = 0
            total_tokens = 0
            is_sealed = False
            version = "1.18.2"

            try:
                # Health
                r_h = requests.get(f"{v_addr}/v1/sys/health", verify=False, timeout=4)
                if r_h.status_code in [200, 429, 473]:
                    h_data = r_h.json()
                    is_sealed = h_data.get("sealed", False)
                    version = h_data.get("version", version)
            except Exception:
                pass

            try:
                # Orgs & Secrets count
                r_o = requests.get(f"{v_addr}/v1/secret/metadata?list=true", headers=v_headers, verify=False, timeout=4)
                if r_o.status_code == 200:
                    orgs = r_o.json().get("data", {}).get("keys", [])
                    total_orgs = len(orgs)
                    for o in orgs:
                        r_s = requests.get(f"{v_addr}/v1/secret/metadata/{o.rstrip('/')}?list=true", headers=v_headers, verify=False, timeout=4)
                        if r_s.status_code == 200:
                            total_secrets += len(r_s.json().get("data", {}).get("keys", []))
            except Exception:
                pass

            try:
                # Tokens count
                r_t = requests.get(f"{v_addr}/v1/auth/token/accessors?list=true", headers=v_headers, verify=False, timeout=4)
                if r_t.status_code == 200:
                    total_tokens = len(r_t.json().get("data", {}).get("keys", []))
            except Exception:
                pass

            return self.send_json(200, {
                "total_orgs": total_orgs,
                "total_secrets": total_secrets,
                "total_tokens": total_tokens,
                "sealed": is_sealed,
                "version": version
            })

        # 2. Organizations
        elif path == "/api/organizations":
            try:
                r = requests.get(f"{v_addr}/v1/secret/metadata?list=true", headers=v_headers, verify=False, timeout=5)
                if r.status_code == 200:
                    keys = [k.rstrip("/") for k in r.json().get("data", {}).get("keys", [])]
                    return self.send_json(200, {"organizations": sorted(keys)})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})
            return self.send_json(200, {"organizations": []})

        # 3. Services for Org
        elif path == "/api/services":
            org = query.get("org", [""])[0]
            if not org:
                return self.send_json(400, {"error": "org is required"})
            try:
                r = requests.get(f"{v_addr}/v1/secret/metadata/{org}?list=true", headers=v_headers, verify=False, timeout=5)
                if r.status_code == 200:
                    keys = [k.rstrip("/") for k in r.json().get("data", {}).get("keys", [])]
                    return self.send_json(200, {"services": sorted(keys)})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})
            return self.send_json(200, {"services": []})

        # 4. Secret Details
        elif path == "/api/secrets":
            org = query.get("org", [""])[0]
            service = query.get("service", [""])[0]
            if not org or not service:
                return self.send_json(400, {"error": "org and service are required"})
            try:
                r = requests.get(f"{v_addr}/v1/secret/data/{org}/{service}", headers=v_headers, verify=False, timeout=5)
                if r.status_code == 200:
                    res_json = r.json()
                    data = res_json.get("data", {}).get("data", {})
                    metadata = res_json.get("data", {}).get("metadata", {})
                    return self.send_json(200, {"data": data, "metadata": metadata})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})
            return self.send_json(404, {"error": "Secret not found"})

        # 5. Tokens list
        elif path == "/api/tokens":
            try:
                r = requests.get(f"{v_addr}/v1/auth/token/accessors?list=true", headers=v_headers, verify=False, timeout=5)
                if r.status_code == 200:
                    accessors = r.json().get("data", {}).get("keys", [])
                    token_list = []
                    for acc in accessors[:30]:
                        info_r = requests.post(f"{v_addr}/v1/auth/token/lookup-accessor", headers=v_headers, json={"accessor": acc}, verify=False, timeout=3)
                        if info_r.status_code == 200:
                            td = info_r.json().get("data", {})
                            token_list.append({
                                "accessor": acc,
                                "display_name": td.get("display_name", "token"),
                                "policies": td.get("policies", []),
                                "ttl": td.get("ttl", 0)
                            })
                    return self.send_json(200, {"tokens": token_list})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})
            return self.send_json(200, {"tokens": []})

        # 6. AppRoles list
        elif path == "/api/approles":
            try:
                r = requests.get(f"{v_addr}/v1/auth/approle/role?list=true", headers=v_headers, verify=False, timeout=5)
                if r.status_code == 200:
                    roles = r.json().get("data", {}).get("keys", [])
                    role_list = []
                    for r_name in roles:
                        r_id_res = requests.get(f"{v_addr}/v1/auth/approle/role/{r_name}/role-id", headers=v_headers, verify=False, timeout=3)
                        role_id = r_id_res.json().get("data", {}).get("role_id", "") if r_id_res.status_code == 200 else ""
                        
                        r_info = requests.get(f"{v_addr}/v1/auth/approle/role/{r_name}", headers=v_headers, verify=False, timeout=3)
                        policies = r_info.json().get("data", {}).get("token_policies", []) if r_info.status_code == 200 else []
                        role_list.append({
                            "role_name": r_name,
                            "role_id": role_id,
                            "policies": policies
                        })
                    return self.send_json(200, {"roles": role_list})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})
            return self.send_json(200, {"roles": []})

        # 7. Policies
        elif path == "/api/policies":
            p_name = query.get("name", [""])[0]
            if p_name:
                try:
                    r = requests.get(f"{v_addr}/v1/sys/policies/acl/{p_name}", headers=v_headers, verify=False, timeout=4)
                    if r.status_code == 200:
                        return self.send_json(200, {"policy": r.json().get("data", {}).get("policy", "")})
                except Exception as e:
                    return self.send_json(500, {"error": str(e)})
                return self.send_json(404, {"error": "Policy not found"})
            else:
                try:
                    r = requests.get(f"{v_addr}/v1/sys/policies/acl?list=true", headers=v_headers, verify=False, timeout=4)
                    if r.status_code == 200:
                        keys = r.json().get("data", {}).get("keys", [])
                        return self.send_json(200, {"policies": sorted(keys)})
                except Exception as e:
                    return self.send_json(500, {"error": str(e)})
                return self.send_json(200, {"policies": []})

        # 8. Audit logs
        elif path == "/api/audit":
            logs = []
            if os.path.exists(AUDIT_LOG_FILE):
                try:
                    cmd = f"tail -n 25 {AUDIT_LOG_FILE}"
                    out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
                    for line in out.strip().splitlines():
                        if not line.strip(): continue
                        try:
                            entry = json.loads(line)
                            req = entry.get("request", {})
                            auth = entry.get("auth", {})
                            logs.append({
                                "time": entry.get("time", "")[:19].replace("T", " "),
                                "client_ip": req.get("remote_address", "unknown"),
                                "operation": req.get("operation", "read"),
                                "path": req.get("path", "")[:32],
                                "auth_identity": auth.get("display_name", "unauth")
                            })
                        except Exception:
                            pass
                except Exception:
                    pass
            return self.send_json(200, {"logs": list(reversed(logs))})

        # 9. Password generator
        elif path == "/api/generator/password":
            length = int(query.get("length", [24])[0])
            chars = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
            pwd = ''.join(secrets.choice(chars) for _ in range(length))
            return self.send_json(200, {"password": pwd})

        # 10. Client IP detection
        elif path == "/api/my-ip":
            return self.send_json(200, {"ip": self.get_client_ip()})

        # 11. Doctor diagnostics
        elif path == "/api/doctor":
            checks = []
            
            # 1. Systemd Vault
            is_active = False
            try:
                res = subprocess.run("systemctl is-active vault", shell=True, capture_output=True, text=True)
                is_active = res.stdout.strip() == "active"
            except Exception:
                is_active = True
            checks.append({"title": "Vault Xizmati (systemd)", "desc": "Vault asosiy jarayoni ishlab turibdi", "ok": is_active})

            # 2. Seal & Cluster
            is_unsealed = False
            cluster_name = "SarvarTech-Vault-Cluster"
            vault_ver = "2.1.1"
            try:
                r_h = requests.get(f"{v_addr}/v1/sys/health", verify=False, timeout=3)
                if r_h.status_code in [200, 429, 473]:
                    h_json = r_h.json()
                    is_unsealed = not h_json.get("sealed", True)
                    cluster_name = h_json.get("cluster_name", cluster_name)
                    vault_ver = h_json.get("version", vault_ver)
            except Exception:
                pass
            checks.append({"title": "Vault Muhr Holati (Seal)", "desc": f"Baza ochiq (Unsealed), Shifrlash kalitlari faol. Versiya: {vault_ver}", "ok": is_unsealed})

            # 3. Audit Logging
            has_audit = os.path.exists(AUDIT_LOG_FILE)
            checks.append({"title": "Audit Log Tizimi", "desc": f"Xavfsizlik audit qaydlari yozilmoqda ({AUDIT_LOG_FILE})", "ok": has_audit})

            # 4. Auto-unseal
            is_auto = False
            try:
                res = subprocess.run("systemctl is-active vault-auto-unseal", shell=True, capture_output=True, text=True)
                is_auto = res.stdout.strip() == "active"
            except Exception:
                is_auto = True
            checks.append({"title": "Auto-Unseal Xizmati", "desc": "Server qayta yonganda baza avtomatik ochiladi (vault-auto-unseal.service)", "ok": is_auto})

            # 5. Reverse proxy
            is_nginx = False
            try:
                res = subprocess.run("systemctl is-active nginx", shell=True, capture_output=True, text=True)
                is_nginx = res.stdout.strip() == "active"
            except Exception:
                is_nginx = True
            checks.append({"title": "Nginx HTTPS Reverse Proxy", "desc": "Port 443 va /app/ web konsol yo'naltirilgan", "ok": is_nginx})

            # 6. Disk Space
            disk_info = "OK"
            try:
                df = subprocess.check_output("df -h / | awk 'NR==2 {print $4 \" bo\\'sh (\" $5 \" band)\"}'", shell=True, text=True).strip()
                disk_info = f"Disk sig'imi: {df}"
            except Exception:
                pass
            checks.append({"title": "Server Disk Xotirasi", "desc": disk_info, "ok": True})

            # 7. Memory RAM
            ram_info = "OK"
            try:
                free = subprocess.check_output("free -h | awk '/^Mem:/ {print $3 \" / \" $2}'", shell=True, text=True).strip()
                ram_info = f"Operativ xotira (RAM): {free} ishlatilmoqda"
            except Exception:
                pass
            checks.append({"title": "Server RAM Bandligi", "desc": ram_info, "ok": True})

            return self.send_json(200, {"checks": checks, "version": vault_ver, "cluster": cluster_name})

        # 11. Full Backup Download
        elif path == "/api/backup":
            backup_data = {"timestamp": datetime.datetime.now().isoformat(), "organizations": {}}
            try:
                r_o = requests.get(f"{v_addr}/v1/secret/metadata?list=true", headers=v_headers, verify=False, timeout=5)
                if r_o.status_code == 200:
                    orgs = [k.rstrip("/") for k in r_o.json().get("data", {}).get("keys", [])]
                    for org in orgs:
                        backup_data["organizations"][org] = {}
                        r_s = requests.get(f"{v_addr}/v1/secret/metadata/{org}?list=true", headers=v_headers, verify=False, timeout=5)
                        if r_s.status_code == 200:
                            for srv in r_s.json().get("data", {}).get("keys", []):
                                s_clean = srv.rstrip("/")
                                r_data = requests.get(f"{v_addr}/v1/secret/data/{org}/{s_clean}", headers=v_headers, verify=False, timeout=5)
                                if r_data.status_code == 200:
                                    backup_data["organizations"][org][s_clean] = r_data.json().get("data", {}).get("data", {})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})

            content = json.dumps(backup_data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", f"attachment; filename=vault_backup_{int(time.time())}.json")
            self.end_headers()
            self.wfile.write(content)
            return

        return self.send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        v_addr, v_token = self.get_vault_context()
        v_headers = {"X-Vault-Token": v_token, "Content-Type": "application/json"}

        # 1. Verify session
        if path == "/api/auth/verify":
            req_addr = body.get("addr", v_addr).rstrip("/")
            req_token = body.get("token", v_token)
            try:
                r = requests.get(f"{req_addr}/v1/auth/token/lookup-self", headers={"X-Vault-Token": req_token}, verify=False, timeout=5)
                if r.status_code == 200:
                    user_data = r.json().get("data", {})
                    return self.send_json(200, {"valid": True, "data": user_data})
            except Exception as e:
                return self.send_json(200, {"valid": False, "error": str(e)})
            return self.send_json(200, {"valid": False})

        # 2. Create Organization
        elif path == "/api/organizations":
            name = body.get("name", "").strip().lower()
            init_srv = body.get("initial_service", "core-api").strip().lower()
            if not name:
                return self.send_json(400, {"error": "name is required"})
            
            # Setup policies
            self.ensure_policies(v_addr, v_token, name, init_srv)

            # Create initial secret
            sec_payload = {
                "data": {
                    "organization": name,
                    "service": init_srv,
                    "created_at": datetime.datetime.now().isoformat()
                }
            }
            try:
                r = requests.post(f"{v_addr}/v1/secret/data/{name}/{init_srv}", headers=v_headers, json=sec_payload, verify=False, timeout=5)
                return self.send_json(200, {"success": r.status_code in [200, 204]})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})

        # 3. Create or Update Secret
        elif path == "/api/secrets":
            org = body.get("org", "").strip().lower()
            service = body.get("service", "").strip().lower()
            sec_data = body.get("data", {})
            if not org or not service:
                return self.send_json(400, {"error": "org and service are required"})

            # Ensure policies exist
            self.ensure_policies(v_addr, v_token, org, service)

            try:
                r = requests.post(f"{v_addr}/v1/secret/data/{org}/{service}", headers=v_headers, json={"data": sec_data}, verify=False, timeout=5)
                return self.send_json(200, {"success": r.status_code in [200, 204]})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})

        # 4. Create Token
        elif path == "/api/tokens/create":
            org = body.get("org")
            service = body.get("service")
            policy = body.get("policy", "default")
            ttl = body.get("ttl", "720h")
            num_uses = int(body.get("num_uses", 0))
            renewable = bool(body.get("renewable", True))
            wrap_ttl = body.get("wrap_ttl", "").strip()
            display_name = body.get("display_name", f"{org}-{service}-app")

            self.ensure_policies(v_addr, v_token, org, service)

            req_headers = dict(v_headers)
            if wrap_ttl:
                req_headers["X-Vault-Wrap-TTL"] = wrap_ttl

            token_payload = {
                "policies": [policy],
                "ttl": ttl,
                "num_uses": num_uses,
                "renewable": renewable,
                "display_name": display_name
            }

            r = requests.post(f"{v_addr}/v1/auth/token/create", headers=req_headers, json=token_payload, verify=False, timeout=5)

            if r.status_code in [200, 204]:
                res_data = r.json()
                wrap_info = res_data.get("wrap_info")
                if wrap_info:
                    return self.send_json(200, {
                        "wrapped": True,
                        "client_token": wrap_info.get("token"),
                        "accessor": wrap_info.get("accessor"),
                        "wrap_ttl": wrap_info.get("ttl"),
                        "num_uses": num_uses,
                        "ttl": ttl,
                        "renewable": renewable
                    })
                auth_d = res_data.get("auth", {})
                return self.send_json(200, {
                    "wrapped": False,
                    "client_token": auth_d.get("client_token"),
                    "accessor": auth_d.get("accessor"),
                    "num_uses": auth_d.get("num_uses", num_uses),
                    "ttl": ttl,
                    "renewable": auth_d.get("renewable", renewable)
                })
            return self.send_json(500, {"error": r.text})

        # 5. Revoke Token
        elif path == "/api/tokens/revoke":
            accessor = body.get("accessor")
            if not accessor:
                return self.send_json(400, {"error": "accessor is required"})
            r = requests.post(f"{v_addr}/v1/auth/token/revoke-accessor", headers=v_headers, json={"accessor": accessor}, verify=False, timeout=5)
            return self.send_json(200, {"success": r.status_code in [200, 204]})

        # 6. Create AppRole
        elif path == "/api/approles/create":
            role_name = body.get("role_name")
            policy = body.get("policy")
            token_ttl = body.get("token_ttl", "24h")
            token_max_ttl = body.get("token_max_ttl", "720h")
            secret_id_ttl = body.get("secret_id_ttl", "24h")
            secret_id_num_uses = int(body.get("secret_id_num_uses", 0))
            token_num_uses = int(body.get("token_num_uses", 0))

            role_payload = {
                "token_policies": [policy],
                "token_ttl": token_ttl,
                "token_max_ttl": token_max_ttl,
                "token_num_uses": token_num_uses,
                "secret_id_num_uses": secret_id_num_uses,
                "secret_id_ttl": secret_id_ttl,
                "token_bound_cidrs": [],
                "secret_id_bound_cidrs": []
            }
            sec_payload = {
                "ttl": secret_id_ttl,
                "num_uses": secret_id_num_uses
            }

            requests.post(f"{v_addr}/v1/auth/approle/role/{role_name}", headers=v_headers, json=role_payload, verify=False, timeout=5)
            r_id_res = requests.get(f"{v_addr}/v1/auth/approle/role/{role_name}/role-id", headers=v_headers, verify=False, timeout=5)
            role_id = r_id_res.json().get("data", {}).get("role_id", "")

            sec_id_res = requests.post(f"{v_addr}/v1/auth/approle/role/{role_name}/secret-id", headers=v_headers, json=sec_payload, verify=False, timeout=5)
            secret_id = sec_id_res.json().get("data", {}).get("secret_id", "")

            return self.send_json(200, {
                "role_id": role_id,
                "secret_id": secret_id,
                "token_ttl": token_ttl,
                "secret_id_ttl": secret_id_ttl,
                "secret_id_num_uses": secret_id_num_uses
            })

        # 7. Generate Secret ID for AppRole
        elif path == "/api/approles/secret-id":
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            role_name = query.get("role_name", [""])[0]
            ttl = query.get("ttl", ["24h"])[0]
            num_uses = int(query.get("num_uses", ["0"])[0])
            sec_id_res = requests.post(f"{v_addr}/v1/auth/approle/role/{role_name}/secret-id", headers=v_headers, json={"ttl": ttl, "num_uses": num_uses}, verify=False, timeout=5)
            if sec_id_res.status_code == 200:
                secret_id = sec_id_res.json().get("data", {}).get("secret_id", "")
                return self.send_json(200, {"secret_id": secret_id, "ttl": ttl, "num_uses": num_uses})
            return self.send_json(500, {"error": "Could not generate secret-id"})

        # 8. Restore from JSON
        elif path == "/api/restore":
            orgs = body.get("organizations", {})
            for org, services in orgs.items():
                for srv, sdata in services.items():
                    self.ensure_policies(v_addr, v_token, org, srv)
                    requests.post(f"{v_addr}/v1/secret/data/{org}/{srv}", headers=v_headers, json={"data": sdata}, verify=False, timeout=5)
            return self.send_json(200, {"success": True})

        # 9. Test Token / Secret Access
        elif path == "/api/test-token-access":
            test_token = body.get("token") or v_token
            path_to_test = body.get("path", "").strip().lstrip("/")
            t0 = time.time()
            try:
                r = requests.get(f"{v_addr}/v1/{path_to_test}", headers={"X-Vault-Token": test_token}, verify=False, timeout=5)
                latency_ms = round((time.time() - t0) * 1000, 1)
                data = None
                try:
                    data = r.json()
                except Exception:
                    data = r.text
                err_msg = None
                if r.status_code != 200:
                    if isinstance(data, dict) and data.get("errors"):
                        err_msg = data["errors"][0] if len(data["errors"]) > 0 else "Noma'lum xatolik"
                    elif isinstance(data, dict):
                        err_msg = data.get("error", str(data))
                    else:
                        err_msg = str(data)
                return self.send_json(200, {
                    "status_code": r.status_code,
                    "latency_ms": latency_ms,
                    "success": r.status_code == 200,
                    "data": data if r.status_code == 200 else None,
                    "error": err_msg
                })
            except Exception as e:
                return self.send_json(200, {
                    "status_code": 500,
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                    "success": False,
                    "error": str(e)
                })

        # 10. Create / Update Policy
        elif path == "/api/policies":
            p_name = body.get("name", "").strip()
            policy_text = body.get("policy", "")
            if not p_name or not policy_text:
                return self.send_json(400, {"error": "name and policy are required"})
            try:
                r = requests.put(f"{v_addr}/v1/sys/policies/acl/{p_name}", headers=v_headers, json={"policy": policy_text}, verify=False, timeout=5)
                return self.send_json(200, {"success": r.status_code in [200, 204], "error": r.text if r.status_code not in [200, 204] else None})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})

        return self.send_json(404, {"error": "Endpoint not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        v_addr, v_token = self.get_vault_context()
        v_headers = {"X-Vault-Token": v_token, "Content-Type": "application/json"}

        if path == "/api/secrets":
            org = body.get("org")
            service = body.get("service")
            if not org or not service:
                return self.send_json(400, {"error": "org and service are required"})
            r = requests.delete(f"{v_addr}/v1/secret/metadata/{org}/{service}", headers=v_headers, verify=False, timeout=5)
            return self.send_json(200, {"success": r.status_code in [200, 204]})

        elif path == "/api/policies":
            p_name = body.get("name", "").strip()
            if not p_name:
                return self.send_json(400, {"error": "name is required"})
            if p_name in ["root", "default"]:
                return self.send_json(400, {"error": "Root va Default asosiy tizim policy'larini o'chirib bo'lmaydi!"})
            try:
                r = requests.delete(f"{v_addr}/v1/sys/policies/acl/{p_name}", headers=v_headers, verify=False, timeout=5)
                return self.send_json(200, {"success": r.status_code in [200, 204], "error": r.text if r.status_code not in [200, 204] else None})
            except Exception as e:
                return self.send_json(500, {"error": str(e)})

        return self.send_json(404, {"error": "Endpoint not found"})

    def ensure_policies(self, v_addr, v_token, org, service):
        if not org or not service: return
        headers = {"X-Vault-Token": v_token, "Content-Type": "application/json"}
        p_admin = f"""path "secret/data/{org}/*" {{ capabilities = ["create", "read", "update", "delete", "list"] }}\npath "secret/metadata/{org}/*" {{ capabilities = ["list", "read", "delete"] }}"""
        p_rw = f"""path "secret/data/{org}/{service}" {{ capabilities = ["create", "read", "update", "delete", "list"] }}\npath "secret/metadata/{org}/{service}" {{ capabilities = ["read", "list"] }}"""
        p_ro = f"""path "secret/data/{org}/{service}" {{ capabilities = ["read", "list"] }}\npath "secret/metadata/{org}/{service}" {{ capabilities = ["read", "list"] }}"""
        try:
            requests.put(f"{v_addr}/v1/sys/policies/acl/policy-{org}-admin", headers=headers, json={"policy": p_admin}, verify=False, timeout=3)
            requests.put(f"{v_addr}/v1/sys/policies/acl/policy-{org}-{service}-rw", headers=headers, json={"policy": p_rw}, verify=False, timeout=3)
            requests.put(f"{v_addr}/v1/sys/policies/acl/policy-{org}-{service}-ro", headers=headers, json={"policy": p_ro}, verify=False, timeout=3)
        except Exception:
            pass

def run_server(port=PORT):
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, VaultWebHandler)
    print(f"\n=======================================================")
    print(f" 🌐 VAULT ENTERPRISE WEB CONSOLE ISHGA TUSHDI")
    print(f"=======================================================")
    print(f"  Mahalliy URL:   http://localhost:{port}")
    print(f"  Tarmoq URL:     http://127.0.0.1:{port}")
    print(f"  Web papkasi:    {WEB_DIR}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nWeb server to'xtatildi.")
        httpd.server_close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else PORT
    run_server(p)
