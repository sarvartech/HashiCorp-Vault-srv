import os
import shutil

source = r"c:\Users\user\Documents\vault-srv\vault_panel.py"

destinations = [
    r"C:\Users\user\Desktop\vault_panel.py",
    r"C:\Users\user\Downloads\vault_panel.py",
    r"C:\Users\user\OneDrive\Ishchi stol\vault_panel.py",
    r"C:\Users\user\OneDrive\Desktop\vault_panel.py"
]

for dest in destinations:
    try:
        folder = os.path.dirname(dest)
        if os.path.exists(folder):
            shutil.copy2(source, dest)
            print(f"COPIED to: {dest} (Exists: {os.path.exists(dest)}, Size: {os.path.getsize(dest)})")
    except Exception as e:
        print(f"Error for {dest}: {e}")
