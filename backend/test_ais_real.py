#!/usr/bin/env python3
from curl_cffi import requests
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('/root/.env.citafast')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Obtener cuenta activa
r = sb.table('cuentas_citafast').select('email,country,facility_id,schedule_id,proxies').eq('is_active',True).execute()

for c in r.data:
    print(f"\n{'='*50}")
    print(f"📧 {c['email']}")
    print(f"   country: {c['country']}")
    print(f"   facility_id: {c['facility_id']}")
    print(f"   schedule_id: {c['schedule_id']}")
    
    base_url = f"https://ais.usvisa-info.com/en-{c['country']}/niv"
    print(f"   URL: {base_url}")
    
    # Probar home
    r1 = requests.get(f"{base_url}/users/sign_in", impersonate="chrome120", timeout=15)
    print(f"   Home: {r1.status_code}")
    
    # Probar API fechas
    if c['schedule_id'] and c['facility_id']:
        url = f"{base_url}/schedule/{c['schedule_id']}/appointment/days/{c['facility_id']}.json"
        r2 = requests.get(url, impersonate="chrome120", timeout=15)
        print(f"   API fechas: {r2.status_code} → {len(r2.json()) if r2.status_code==200 else 'error'}")
        if r2.status_code == 200 and r2.json():
            print(f"   🎯 Primera fecha: {r2.json()[0].get('date')}")
