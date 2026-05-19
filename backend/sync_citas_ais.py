#!/usr/bin/env python3
"""
Sincroniza citas reales de AIS hacia Supabase
Ejecutar: python3 /root/sync_citas_ais.py
"""
import os, requests, urllib3, hashlib, time
urllib3.disable_warnings()
from dotenv import load_dotenv; load_dotenv('/root/.env.citafast')
from supabase import create_client
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from datetime import datetime

sb  = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
URL = 'https://ais.usvisa-info.com/en-do/niv'

def bd_proxy(n=0):
    sess = hashlib.md5(f"sync_{n}_{int(time.time())//600}".encode()).hexdigest()[:10]
    u = f'brd-customer-hl_d36aad6c-zone-residential_proxy2-country-us-session-{sess}'
    return {'http':f'http://{u}:yrkzbddify53@brd.superproxy.io:33335',
            'https':f'http://{u}:yrkzbddify53@brd.superproxy.io:33335'}

def sync_cuenta(c, idx):
    email = c.get('email','')
    sid   = c.get('schedule_id','')
    fac   = c.get('facility_id', 138)

    s = requests.Session()
    s.proxies = bd_proxy(idx)
    s.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

    try:
        # Login
        r1 = s.get(f'{URL}/users/sign_in', verify=False, timeout=15)
        csrf = BeautifulSoup(r1.text,'html.parser').find('meta',{'name':'csrf-token'})
        if not csrf: return None, 'Sin CSRF'

        ck = r1.headers.get('set-cookie','')
        r2 = s.post(f'{URL}/users/sign_in', verify=False,
            headers={'X-CSRF-Token':csrf['content'],'Cookie':ck,
                     'Content-Type':'application/x-www-form-urlencoded'},
            data=urlencode({'user[email]':email,'user[password]':c['password'],
                           'policy_confirmed':'1','commit':'Sign In'}), timeout=15)

        if 'locked' in r2.text.lower():
            idx2 = r2.text.lower().find('locked until')
            until = r2.text[idx2+12:idx2+60].strip().split('<')[0].strip() if idx2>0 else '?'
            return None, f'Bloqueada hasta {until}'

        if 'window.location' not in r2.text:
            return None, 'Login rechazado'

        ck2 = r2.headers.get('set-cookie','') or ck

        # Dashboard — obtener cita real
        r_dash = s.get(f'{URL}/groups/{sid}', verify=False,
            headers={'Cookie':ck2}, timeout=12)
        soup = BeautifulSoup(r_dash.text, 'html.parser')

        # Buscar fecha de cita en el HTML
        cita_real = None
        for el in soup.find_all(['p','div','li','td']):
            txt = el.get_text(strip=True)
            if any(m in txt for m in ['January','February','March','April','May',
                                       'June','July','August','September','October',
                                       'November','December']):
                if any(y in txt for y in ['2025','2026','2027','2028']):
                    if len(txt) < 80:
                        cita_real = txt
                        break

        # Schedule ID real desde la URL del dashboard
        new_sid = sid
        if r_dash.url and '/schedule/' in str(r_dash.url):
            import re
            m = re.search(r'/schedule/(\d+)', str(r_dash.url))
            if m: new_sid = m.group(1)

        return {
            'last_appointment_date': cita_real,
            'schedule_id': new_sid,
            'updated_at': datetime.now().isoformat()
        }, 'OK'

    except Exception as e:
        return None, str(e)[:60]

def main():
    print(f"SYNC CITAS AIS → BD — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*60)

    r = sb.table('cuentas_citafast').select(
        'id,email,password,schedule_id,facility_id,last_appointment_date,is_active'
    ).eq('is_active', True).execute()

    actualizadas = 0
    sin_cambio   = 0
    errores      = 0

    for i, c in enumerate(r.data):
        email    = c.get('email','')
        cita_bd  = c.get('last_appointment_date','')
        print(f"[{i+1:02d}/{len(r.data)}] {email[:40]:40}", end=' ')

        data, msg = sync_cuenta(c, i)

        if msg != 'OK':
            print(f"⚠️  {msg}")
            errores += 1
        else:
            cita_nueva = data.get('last_appointment_date')
            sid_nuevo  = data.get('schedule_id')

            if cita_nueva and cita_nueva != cita_bd:
                sb.table('cuentas_citafast').update(data).eq('id', c['id']).execute()
                print(f"✅ Actualizada: {cita_nueva[:40]}")
                actualizadas += 1
            else:
                # Actualizar solo schedule_id si cambió
                if sid_nuevo and str(sid_nuevo) != str(c.get('schedule_id','')):
                    sb.table('cuentas_citafast').update({
                        'schedule_id': sid_nuevo
                    }).eq('id', c['id']).execute()
                    print(f"🔄 SID: {sid_nuevo}")
                else:
                    print(f"— Sin cambios | BD: {str(cita_bd)[:30]}")
                sin_cambio += 1

        time.sleep(3)

    print(f"\nRESULTADO:")
    print(f"  ✅ Actualizadas: {actualizadas}")
    print(f"  — Sin cambios:   {sin_cambio}")
    print(f"  ⚠️  Errores:      {errores}")

if __name__ == '__main__':
    main()
