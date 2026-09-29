import os

panel_path = r"c:\Users\user\Documents\vault-srv\vault_panel.py"
with open(panel_path, "r", encoding="utf-8") as f:
    panel_code = f.read()

reinstall_path = r"c:\Users\user\Documents\vault-srv\reinstall_vault.py"
with open(reinstall_path, "r", encoding="utf-8") as f:
    reinstall_code = f.read()

# Replace step 8 in reinstall_vault.py to write the embedded code directly
old_step8 = """    # 8. Setup CLI-Panel
    print_step("8. CLI-Panelni o'rnatish...")
    src_panel = "./vault_panel.py" if os.path.exists("./vault_panel.py") else "/tmp/vault_panel.py"
    if os.path.exists(src_panel):
        shutil.copy(src_panel, "/usr/local/bin/vault-panel.py")
        run_cmd("chmod +x /usr/local/bin/vault-panel.py")
        with open("/usr/local/bin/vault-panel", "w") as f:
            f.write("#!/bin/bash\\nexec python3 /usr/local/bin/vault-panel.py \\\"$@\\\"\\n")
        run_cmd("chmod +x /usr/local/bin/vault-panel")
        print_ok("CLI-Panel muvaffaqiyatli o'rnatildi.")"""

new_step8 = f'''    # 8. Setup CLI-Panel (Embedded Standalone)
    print_step("8. CLI-Panelni o'rnatish...")
    with open("/usr/local/bin/vault-panel.py", "w", encoding="utf-8") as f:
        f.write({repr(panel_code)})
    run_cmd("chmod +x /usr/local/bin/vault-panel.py")
    with open("/usr/local/bin/vault-panel", "w") as f:
        f.write("#!/bin/bash\\nexec python3 /usr/local/bin/vault-panel.py \\\"$@\\\"\\n")
    run_cmd("chmod +x /usr/local/bin/vault-panel")
    print_ok("CLI-Panel muvaffaqiyatli o'rnatildi.")'''

if old_step8 in reinstall_code:
    updated_code = reinstall_code.replace(old_step8, new_step8)
    with open(reinstall_path, "w", encoding="utf-8") as f:
        f.write(updated_code)
    
    # Also update on Desktop and Downloads
    for p in [r"C:\Users\user\Desktop\reinstall_vault.py", r"C:\Users\user\OneDrive\Ishchi stol\reinstall_vault.py", r"C:\Users\user\Downloads\reinstall_vault.py"]:
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(updated_code)
            print(f"Updated standalone reinstall_vault.py at {p}")
        except Exception as e:
            print(f"Error {p}: {e}")
else:
    print("old_step8 not found in reinstall_code")
