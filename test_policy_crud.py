import requests

import os
addr = 'http://192.168.86.128:5000'
h = {'X-Vault-Token': os.environ.get("VAULT_TOKEN", "YOUR_VAULT_ROOT_TOKEN")}

# 1. List
r_list = requests.get(f'{addr}/api/policies', headers=h)
print('1. List policies:', r_list.status_code, 'Count:', len(r_list.json().get('policies', [])))

# 2. Create
p = 'path "secret/data/test/*" { capabilities = ["read"] }'
r_post = requests.post(f'{addr}/api/policies', headers=h, json={'name': 'test-demo-pol', 'policy': p})
print('2. Create policy status:', r_post.status_code, r_post.json())

# 3. Read
r_get = requests.get(f'{addr}/api/policies?name=test-demo-pol', headers=h)
print('3. Read policy status:', r_get.status_code, r_get.json().get('policy'))

# 4. Delete
r_del = requests.delete(f'{addr}/api/policies', headers=h, json={'name': 'test-demo-pol'})
print('4. Delete policy status:', r_del.status_code, r_del.json())
