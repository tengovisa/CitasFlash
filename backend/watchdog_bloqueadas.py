#!/usr/bin/env python3
"""
Watchdog CitasFlash — cada 30 min
Revisa cuentas bloqueadas en AIS
Si se liberan → reactiva + Telegram
"""
import os, requests, time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv('/root/.env.citafast')
from supabase import create_client
from bs4 import BeautifulSoup
from urllib.parse import urlencode

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
TG_TOKEN = os.getenv('TELEGRAM_TOKEN','')
TG_CHAT  = os.getenv('TELEGRAM_CHAT_ID','')

def telegram(msg):
    if not TG_TOKEN or not TG_CHAT: return
    try:
        requests.post(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
            json={'chat_id':TG_CHAT,'text':msg,'parse_mode':'Markdown'}, timeout=10)
    except: pass

def check_calendar(email, password, schedule_id, facility_id, proxies_str):
    pool = [p.strip() for p in proxies_str.split(',') if p.strip()]
    dc   = [p for p in pool if 'DC:' in p]
    res  = [p for p in pool if 'DC:' not in p]
    px_list = dc + res  # DC primero para watchdog
    
    for px_raw in px_list[:5]:
        px = px_raw.replace('DC:','')
        try:
            s = requests.Session()
            s.proxies = {'http':f'http://{px}','https':f'http://{px}'}
            url = 'https://ais.usvisa-info.com/en-do/niv'
            r1 = s.get(f'{url}/users/sign_in', timeout=12)
            csrf = BeautifulSoup(r1.text,'html.parser').find('meta',{'name':'csrf-token'})
            if not csrf: continue
            ck = r1.headers.get('set-cookie','')
            r2 = s.post(f'{url}/users/sign_in',
                headers={'X-CSRF-Token':csrf['content'],'Cookie':ck,'Content-Type':'application/x-www-form-urlencoded'},
                data=urlencode({'user[email]':email,'user[password]':password,'policy_confirmed':'1','commit':'Sign In'}),
                timeout=12)
            if 'Invalid' in r2.text: return 'CREDENCIALES_INVALIDAS'
            ck2 = r2.headers.get('set-cookie','') or ck
            days = f'{url}/schedule/{schedule_id}/appointment/days/{facility_id}.json?appointments[expedite]=false'
            r3 = s.get(days, headers={'Cookie':ck2,'Referer':f'{url}/schedule/{schedule_id}/appointment'}, timeout=10)
            if r3.status_code == 200:
                return 'LIBRE'
            elif r3.status_code in [401,403]:
                return 'BLOQUEADO'
        except: continue
    return 'PROXY_ERROR'

def main():
    ts = datetime.now().strftime('%H:%M')
    print(f'[{ts}] Watchdog iniciado')
    
    # Cuentas bloqueadas
    bloqueadas = sb.table('cuentas_citafast').select(
        'id,email,password,schedule_id,facility_id,proxies,status'
    ).eq('is_active',False).in_('status',['Sin acceso calendario','Bloqueada AIS','Pausa 30min']).execute().data
    
    # Cuentas sin intentos
    sin_intentos = sb.table('cuentas_citafast').select('id,email,status').eq('status','Sin intentos').execute().data
    
    print(f'Bloqueadas: {len(bloqueadas)} | Sin intentos: {len(sin_intentos)}')
    
    if not bloqueadas and not sin_intentos:
        print('Todo OK — sin cuentas bloqueadas')
        return
    
    reactivadas = []
    siguen_bloqueadas = []
    
    for c in bloqueadas:
        email = c['email']
        estado = check_calendar(
            email, c.get('password',''),
            c.get('schedule_id',''), c.get('facility_id',138),
            c.get('proxies','')
        )
        print(f'  {email[:35]:35} → {estado}')
        
        if estado == 'LIBRE':
            sb.table('cuentas_citafast').update({
                'is_active': True,
                'status': 'Activo'
            }).eq('id', c['id']).execute()
            reactivadas.append(email)
        elif estado == 'CREDENCIALES_INVALIDAS':
            sb.table('cuentas_citafast').update({'status':'Error credenciales'}).eq('id',c['id']).execute()
        else:
            siguen_bloqueadas.append(email)
        time.sleep(3)
    
    # Notificar Telegram
    if reactivadas:
        msg = f'✅ *CALENDARIO LIBERADO*\n'
        msg += f'🕐 {datetime.now().strftime("%d/%m %H:%M")}\n\n'
        for e in reactivadas:
            msg += f'  ✅ {e}\n'
        msg += f'\n🔄 {len(reactivadas)} cuenta(s) reactivadas automáticamente'
        telegram(msg)
        print(f'✅ Telegram enviado: {len(reactivadas)} reactivadas')
    
    if siguen_bloqueadas:
        msg = f'📵 *CUENTAS SIN CALENDARIO*\n'
        msg += f'🕐 {datetime.now().strftime("%d/%m %H:%M")}\n\n'
        for e in siguen_bloqueadas[:5]:
            msg += f'  ❌ {e}\n'
        if len(siguen_bloqueadas) > 5:
            msg += f'  ...y {len(siguen_bloqueadas)-5} más\n'
        telegram(msg)
    
    if sin_intentos:
        msg = f'⚠️ *CUENTAS SIN INTENTOS*\n'
        msg += f'🕐 {datetime.now().strftime("%d/%m %H:%M")}\n\n'
        for c in sin_intentos:
            msg += f'  ⚠️ {c["email"]}\n'
        msg += '\nEstas cuentas no pueden reagendar citas.'
        telegram(msg)
        print(f'⚠️ {len(sin_intentos)} cuentas sin intentos — Telegram enviado')

if __name__ == '__main__':
    main()
