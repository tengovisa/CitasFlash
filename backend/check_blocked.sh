#!/bin/bash
python3 << 'PYEOF'
import os, requests
from dotenv import load_dotenv
load_dotenv('/root/.env.citafast')
from supabase import create_client

sb=create_client(os.getenv('SUPABASE_URL'),os.getenv('SUPABASE_KEY'))
TOKEN='8612004045:AAGFmqfUsmefl0YoR2PGTyZd26YDvZQm0Zo'
CHAT='1193245321'

def telegram(msg):
    requests.post(f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        json={'chat_id':CHAT,'text':msg,'parse_mode':'Markdown'},timeout=10)

# Verificar bloqueadas
r=sb.table('cuentas_citafast').select('email,password,schedule_id,proxies').eq('status','Bloqueada AIS').execute()
desbloqueadas=[]
for a in r.data:
    try:
        res=requests.post('http://localhost:8000/cuentas/validar',
            headers={'x-api-key':'CitaFast2026Bot2'},
            json={'email':a['email'],'password':a['password'],
                  'schedule_id':a['schedule_id'],'proxies':a.get('proxies','')},
            timeout=20)
        d=res.json()
        if d.get('puede_calendario'):
            sb.table('cuentas_citafast').update({'is_active':False,'status':'Pendiente de revalidación','max_date':'2026-07-30'}).eq('email',a['email']).execute()
            desbloqueadas.append(a['email'])
            print(f'Desbloqueada: {a["email"]}')
    except: pass

if desbloqueadas:
    msg = f'🔓 *Cuentas desbloqueadas automáticamente:*\n' + '\n'.join(desbloqueadas)
    telegram(msg)
    print(f'Telegram enviado: {len(desbloqueadas)} cuentas')
else:
    print('Sin cambios')
PYEOF
