import os
from dotenv import load_dotenv
load_dotenv('/root/.env.citafast')
from supabase import create_client
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
proxies_raw = [
"82.22.209.32:5862:axihbvupdatacenter:ng8m7kbc1met",
"86.38.26.166:6331:axihbvupdatacenter:ng8m7kbc1met",
"198.37.109.14:6121:axihbvupdatacenter:ng8m7kbc1met",
"45.39.20.151:5580:axihbvupdatacenter:ng8m7kbc1met",
"154.30.1.90:5406:axihbvupdatacenter:ng8m7kbc1met",
"89.249.193.127:5865:axihbvupdatacenter:ng8m7kbc1met",
"46.203.206.114:5559:axihbvupdatacenter:ng8m7kbc1met",
"64.64.115.28:5663:axihbvupdatacenter:ng8m7kbc1met",
"45.38.111.165:6080:axihbvupdatacenter:ng8m7kbc1met",
"92.112.228.46:6127:axihbvupdatacenter:ng8m7kbc1met"
]
sb.table('proxies').delete().neq('id',0).execute()
count = 0
for line in proxies_raw:
    parts = line.split(':')
    if len(parts)==4:
        p = f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
        sb.table('proxies').insert({'proxy':p,'type':'datacenter','status':'free','fail_count':0}).execute()
        count += 1
print(f'OK — {count} proxies cargados')
