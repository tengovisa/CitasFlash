import os
from dotenv import load_dotenv
load_dotenv('/root/.env.citafast')
from supabase import create_client
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

dc = []
for archivo in ['/root/dc_proxies.txt', '/root/datacenter.txt']:
    if os.path.exists(archivo):
        with open(archivo) as f:
            for l in f:
                l = l.strip().replace('\r','')
                if l and not l.startswith('DC:'):
                    dc.append(f'DC:{l}')
                elif l.startswith('DC:'):
                    dc.append(l)
        print(f"Leídos {len(dc)} DC de {archivo}")
        break

dc_uniq = list(set(dc))
print(f"DC únicos: {len(dc_uniq)}")

RES = sb.table('cuentas_citafast').select('proxies').eq('is_active',True).limit(1).execute()
pool = (RES.data[0].get('proxies') or '').split(',')
res_only = [p.strip() for p in pool if p.strip() and not p.strip().startswith('DC:')]

pool_final = ','.join(list(set(res_only)) + dc_uniq)
cuentas = sb.table('cuentas_citafast').select('id').eq('is_active',True).execute()
for c in cuentas.data:
    sb.table('cuentas_citafast').update({'proxies': pool_final}).eq('id', c['id']).execute()
print(f"✅ Pool {len(set(res_only))} RES + {len(dc_uniq)} DC asignado a {len(cuentas.data)} cuentas")
