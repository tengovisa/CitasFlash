#!/usr/bin/env python3
"""
Account Health Monitor — CitasFlash Nexus
Detecta bloqueos, pausa cuentas, watchdog 30min, Telegram
"""
import os, time, requests, re
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv('/root/.env.citafast')
from supabase import create_client
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import urllib3
urllib3.disable_warnings()

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
TG_TOKEN = os.getenv('TELEGRAM_TOKEN','')
TG_CHAT  = os.getenv('TELEGRAM_CHAT_ID','')
TABLE    = 'cuentas_citafast'
URL_BASE = 'https://ais.usvisa-info.com/en-do/niv'

# ═══════════════════════════════════════
# ESTADOS DE CUENTA
# ═══════════════════════════════════════
STATES = {
    'active':              {'label':'✅ Activo',              'severity':'ok',      'retry_min':0},
    'locked_login':        {'label':'🔒 Login bloqueado',     'severity':'high',    'retry_min':30},
    'locked_calendar':     {'label':'📵 Calendario bloqueado','severity':'high',    'retry_min':30},
    'locked_booking':      {'label':'🚫 Booking bloqueado',   'severity':'high',    'retry_min':60},
    'no_schedule_id':      {'label':'❓ Sin Schedule ID',     'severity':'medium',  'retry_min':10},
    'session_invalid':     {'label':'⚠️ Sesión inválida',     'severity':'medium',  'retry_min':5},
    'csrf_failed':         {'label':'🔑 CSRF fallido',        'severity':'medium',  'retry_min':5},
    'proxy_error':         {'label':'🌐 Error proxy',         'severity':'low',     'retry_min':2},
    'payment_issue':       {'label':'💳 Problema de acceso',  'severity':'critical','retry_min':120},
    'account_unavailable': {'label':'🚷 Cuenta no disponible','severity':'critical','retry_min':60},
    'unknown_block':       {'label':'❓ Bloqueo desconocido', 'severity':'high',    'retry_min':30},
    'recovery_pending':    {'label':'🔄 Verificando...',      'severity':'medium',  'retry_min':30},
    'recovered':           {'label':'🎉 Recuperada',          'severity':'ok',      'retry_min':0},
    'paused_manual':       {'label':'⏸ Pausada',              'severity':'low',     'retry_min':0},
}

# ═══════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════
def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
            json={'chat_id': TG_CHAT, 'text': msg, 'parse_mode': 'Markdown'},
            timeout=10
        )
        print(f'[TELEGRAM_SENT] {msg[:60]}')
    except Exception as e:
        print(f'[TELEGRAM_ERROR] {e}')

# ═══════════════════════════════════════
# DETECTOR DE ESTADO
# ═══════════════════════════════════════
def detect_state(html, status_code, url, context=''):
    """Analiza respuesta HTTP y clasifica el estado real"""
    html_lower = html.lower() if html else ''

    # HTTP 402 = cuenta bloqueada por AIS (código oficial de bloqueo)
    if status_code == 402:
        lock_match = re.search(r'locked until\s+(.+?)[\.<
]', html_lower)
        lock_until = lock_match.group(1).strip() if lock_match else None
        msg = f'Bloqueada AIS (402) hasta {lock_until}' if lock_until else 'Bloqueada AIS (HTTP 402)'
        return 'locked_login', msg, lock_until

    # Bloqueado por login — detectado en HTML
    if any(x in html_lower for x in ['your account is locked', 'account locked', 'locked until']):
        lock_match = re.search(r'locked until\s+(.+?)[\.<
]', html_lower)
        lock_until = lock_match.group(1).strip() if lock_match else None
        return 'locked_login', f'Cuenta bloqueada hasta {lock_until}', lock_until

    # Problema de pago/acceso
    if any(x in html_lower for x in ['payment', 'billing', 'fee required', 'access denied']):
        return 'payment_issue', 'Problema de pago o acceso', None

    # Sigue en sign_in después del login
    if 'sign_in' in url.lower() or ('sign in' in html_lower and 'password' in html_lower):
        return 'session_invalid', 'Login no procesado — sigue en sign_in', None

    # CSRF ausente
    if context == 'sign_in' and '<meta name="csrf-token"' not in html:
        return 'csrf_failed', 'CSRF token ausente en sign_in', None

    # Calendario bloqueado
    if status_code in [401, 403] and context == 'calendar':
        return 'locked_calendar', f'Calendario HTTP {status_code}', None

    # Redirección inesperada a unsupported
    if 'unsupported' in url.lower() or 'information/unsupported' in url.lower():
        return 'no_schedule_id', 'Redirigido a /unsupported — sin Schedule ID', None

    # Challenge/Captcha
    if any(x in html_lower for x in ['captcha', 'challenge', 'verify you are human', 'recaptcha']):
        return 'account_unavailable', 'Captcha/Challenge detectado', None

    # No hay schedule_id
    if context == 'dashboard' and 'schedule_id' not in html_lower and 'application' not in html_lower:
        return 'no_schedule_id', 'Dashboard OK pero sin schedule_id visible', None

    # OK
    return 'active', 'Acceso correcto', None

# ═══════════════════════════════════════
# VERIFICADOR DE CUENTA
# ═══════════════════════════════════════
def check_account(cuenta):
    email    = cuenta.get('email','')
    password = cuenta.get('password','')
    sid      = cuenta.get('schedule_id','')
    fac      = cuenta.get('facility_id', 138)
    proxies_str = cuenta.get('proxies','')

    # Seleccionar proxy DC primero
    pool = [p.strip() for p in proxies_str.split(',') if p.strip()]
    dc   = [p.replace('DC:','') for p in pool if 'DC:' in p]
    res  = [p for p in pool if 'DC:' not in p]
    px_list = (dc + res)[:5]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'
    }

    # Watchdog usa BrightData rotating — no depende de proxies DC quemados
    import os as _os
    BD_USER = 'brd-customer-hl_d36aad6c-zone-residential_proxy2'
    BD_PASS = 'yrkzbddify53'
    BD_PX   = f'{BD_USER}:{BD_PASS}@brd.superproxy.io:33335'
    px_list_final = [BD_PX] + [p.replace('DC:','') for p in px_list[:2]]

    for px_raw in px_list_final:
        px_url = f'http://{px_raw}'
        s = requests.Session()
        s.proxies = {'http': px_url, 'https': px_url}
        s.headers.update(headers)

        try:
            # PASO 1: GET sign_in
            r1 = s.get(f'{URL_BASE}/users/sign_in', verify=False, timeout=12)
            state, reason, lock_until = detect_state(r1.text, r1.status_code, str(r1.url), 'sign_in')
            if state != 'active':
                return state, reason, lock_until

            csrf = BeautifulSoup(r1.text,'html.parser').find('meta',{'name':'csrf-token'})
            if not csrf:
                return 'csrf_failed', 'Sin CSRF en sign_in', None

            # PASO 2: POST login
            ck = r1.headers.get('set-cookie','')
            r2 = s.post(f'{URL_BASE}/users/sign_in', verify=False,
                headers={'X-CSRF-Token':csrf['content'],'Cookie':ck,'Content-Type':'application/x-www-form-urlencoded'},
                data=urlencode({'user[email]':email,'user[password]':password,'policy_confirmed':'1','commit':'Sign In'}),
                timeout=12)

            if 'Invalid' in r2.text:
                return 'account_unavailable', 'Credenciales inválidas', None

            state, reason, lock_until = detect_state(r2.text, r2.status_code, str(r2.url), 'login')
            if state != 'active':
                return state, reason, lock_until

            if not sid:
                return 'no_schedule_id', 'Sin schedule_id en BD', None

            # PASO 3: GET days.json
            ck2 = r2.headers.get('set-cookie','') or ck
            days = f'{URL_BASE}/schedule/{sid}/appointment/days/{fac}.json?appointments[expedite]=false'
            r3 = s.get(days, verify=False,
                headers={'Cookie':ck2,'Referer':f'{URL_BASE}/schedule/{sid}/appointment'}, timeout=10)

            if r3.status_code in [401, 403]:
                return 'locked_calendar', f'Calendario HTTP {r3.status_code}', None

            if r3.status_code == 200:
                try:
                    fechas = r3.json()
                    return 'active', f'OK — {len(fechas)} fechas disponibles', None
                except:
                    return 'session_invalid', 'Calendar devolvió HTML en vez de JSON', None

            return 'unknown_block', f'HTTP {r3.status_code} inesperado', None

        except requests.exceptions.ProxyError:
            continue  # Probar siguiente proxy
        except requests.exceptions.ConnectionError:
            continue
        except Exception as e:
            return 'unknown_block', str(e)[:80], None

    return 'proxy_error', 'Todos los proxies fallaron', None

# ═══════════════════════════════════════
# ACTUALIZAR ESTADO EN BD
# ═══════════════════════════════════════
def update_account_state(cuenta_id, email, old_state, new_state, reason, lock_until=None):
    state_info = STATES.get(new_state, {})
    retry_min  = state_info.get('retry_min', 30)
    next_check = (datetime.utcnow() + timedelta(minutes=retry_min)).isoformat()
    is_active  = (new_state in ['active','recovered'])
    status_label = state_info.get('label', new_state)

    update = {
        'is_active': is_active,
        'status': status_label,
        'updated_at': datetime.utcnow().isoformat()
    }

    sb.table(TABLE).update(update).eq('id', cuenta_id).execute()

    # Telegram si cambió de estado
    if old_state != new_state:
        emoji = '✅' if new_state == 'active' else '🔴'
        msg = (
            f'{emoji} *CAMBIO DE ESTADO*\n'
            f'📧 {email}\n'
            f'📌 Antes: `{old_state}`\n'
            f'📌 Ahora: `{status_label}`\n'
            f'📝 Motivo: {reason}\n'
            f'🕐 {datetime.now().strftime("%d/%m %H:%M")}'
        )
        if lock_until:
            msg += f'\n🔒 Bloqueado hasta: {lock_until}'
        if new_state == 'active':
            msg += '\n\n🎉 ¡Cuenta reactivada automáticamente!'
        send_telegram(msg)

    print(f'[ACCOUNT_STATE] {email[:35]:35} {old_state} → {new_state} | {reason[:50]}')

# ═══════════════════════════════════════
# WATCHDOG PRINCIPAL
# ═══════════════════════════════════════
def run_watchdog():
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'\n[RECOVERY_CHECK] Iniciando watchdog — {ts}')

    # Cuentas no activas (bloqueadas, pausadas por error)
    r = sb.table(TABLE).select('*').eq('is_active', False).execute()
    candidatas = [c for c in r.data if c.get('status') not in ['Pausado — Proxies en mantenimiento','Pausado','paused_manual']]

    print(f'[RECOVERY_CHECK] Cuentas a verificar: {len(candidatas)}')

    for c in candidatas:
        email    = c.get('email','')
        old_status = c.get('status','unknown')
        print(f'[RECOVERY_CHECK] Verificando: {email[:40]}')

        new_state, reason, lock_until = check_account(c)

        # Mapear estado viejo a código
        old_state = 'unknown_block'
        for code, info in STATES.items():
            if info['label'] == old_status or code == old_status:
                old_state = code
                break

        if new_state == 'active':
            print(f'[RECOVERY_SUCCESS] {email[:40]} — Reactivando')
            update_account_state(c['id'], email, old_state, 'active', reason)
        else:
            print(f'[RECOVERY_STILL_BLOCKED] {email[:40]} — {new_state}: {reason}')
            update_account_state(c['id'], email, old_state, new_state, reason, lock_until)

        time.sleep(5)

    # Resumen final
    r2 = sb.table(TABLE).select('id,is_active').execute()
    activas = len([c for c in r2.data if c['is_active']])
    total   = len(r2.data)
    print(f'[RECOVERY_CHECK] Finalizado — Activas: {activas}/{total}')

    if candidatas:
        send_telegram(
            f'🔄 *WATCHDOG COMPLETADO*\n'
            f'🕐 {datetime.now().strftime("%d/%m %H:%M")}\n'
            f'✅ Activas: {activas}/{total}\n'
            f'🔍 Verificadas: {len(candidatas)}'
        )

if __name__ == '__main__':
    run_watchdog()
