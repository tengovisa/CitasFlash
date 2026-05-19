#!/usr/bin/env python3
"""
NEXUS CRON WORKER — Ejecuta tareas programadas
Corre cada minuto via crontab
"""
import os, sys, subprocess, json, logging
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv

load_dotenv('/root/.env.citafast')
from supabase import create_client

# ── CONFIG ──
TZ = pytz.timezone('America/Santo_Domingo')
LOG_FILE = '/var/log/nexus_cron.log'
LOCK_FILE = '/tmp/nexus_cron.lock'

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [CRON] %(message)s'
)
log = logging.getLogger()

# ── WHITELIST ACCIONES SEGURAS ──
ALLOWED_ACTIONS = {
    'start':       ['systemctl', 'start',   'nexus'],
    'stop':        ['systemctl', 'stop',    'nexus'],
    'restart':     ['systemctl', 'restart', 'nexus'],
    'clean_logs':  ['truncate', '-s', '0', '/root/nexus.log'],
    'rotate_logs': None,  # manejado especial
    'set_config':  None,  # manejado especial
}

DAYS_MAP = {
    'lunes':0,'martes':1,'miercoles':2,'miércoles':2,
    'jueves':3,'viernes':4,'sabado':5,'sábado':5,'domingo':6
}

def get_sb():
    return create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def lock():
    if os.path.exists(LOCK_FILE):
        try:
            age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(LOCK_FILE))).seconds
            if age < 55: return False
        except: pass
    open(LOCK_FILE,'w').write(str(os.getpid()))
    return True

def unlock():
    try: os.remove(LOCK_FILE)
    except: pass

def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.returncode == 0, r.stdout + r.stderr
    except Exception as e:
        return False, str(e)

def apply_set_config(config):
    """Aplica configuración a nexus.py modificando get_speed_mode dinámicamente"""
    mode        = config.get('mode', 'CONSERVADOR')
    workers     = config.get('workers', 1)
    delay       = config.get('delay_seconds', 30.0)
    use_proxies = config.get('use_proxies', True)

    # Escribir override en archivo temporal que nexus.py puede leer
    override = {
        'mode': mode,
        'workers': workers,
        'delay': float(delay),
        'use_proxies': use_proxies,
        'proxy_pool': config.get('proxy_pool',''),
        'pause_outside_window': config.get('pause_outside_window', False),
        'backoff_on_error': config.get('backoff_on_error', True),
        'applied_at': datetime.now().isoformat()
    }
    json.dump(override, open('/root/nexus_cron_override.json','w'), indent=2)
    return True, f"Config aplicada: {mode} | {workers}w | {delay}s"

def rotate_logs():
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    src = '/root/nexus.log'
    dst = f'/root/logs/nexus_{ts}.log'
    os.makedirs('/root/logs', exist_ok=True)
    try:
        os.rename(src, dst)
        open(src,'w').close()
        return True, f"Log rotado a {dst}"
    except Exception as e:
        return False, str(e)

def save_log(sb, cron_id, status, message, command=''):
    try:
        sb.table('cron_nexus_logs').insert({
            'cron_id': cron_id,
            'status': status,
            'message': message,
            'command_executed': command,
            'executed_at': datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        log.error(f"Error guardando log: {e}")

def should_run(task, now, weekday):
    # Verificar día
    days = task.get('days') or []
    if days:
        day_nums = [DAYS_MAP.get(d.lower(), -1) for d in days]
        if weekday not in day_nums:
            return False, 'skipped'

    # Verificar hora inicio
    start = task.get('start_time')
    if start:
        sh, sm = map(int, str(start)[:5].split(':'))
        if (now.hour, now.minute) < (sh, sm):
            return False, 'skipped'

    # Verificar hora fin
    end = task.get('end_time')
    if end and str(end) != 'None':
        eh, em = map(int, str(end)[:5].split(':'))
        if (now.hour, now.minute) > (eh, em):
            return False, 'skipped'

    # Anti-duplicado: no correr si ya corrió en este minuto
    last_run = task.get('last_run')
    if last_run:
        try:
            if isinstance(last_run, str):
                lr = datetime.fromisoformat(last_run.replace('Z','+00:00'))
            else:
                lr = last_run
            lr_local = lr.astimezone(TZ)
            if lr_local.date() == now.date() and lr_local.hour == now.hour and lr_local.minute == now.minute:
                return False, 'skipped'
        except: pass

    return True, 'ok'

def execute_task(task, sb):
    action = task.get('action')
    config = task.get('config') or {}
    task_id = task.get('id')
    name = task.get('name','?')

    log.info(f"Ejecutando: [{name}] acción={action}")

    if action not in ALLOWED_ACTIONS:
        save_log(sb, task_id, 'error', f'Acción no permitida: {action}')
        return

    ok, msg = False, ''

    if action == 'set_config':
        ok, msg = apply_set_config(config)
    elif action == 'rotate_logs':
        ok, msg = rotate_logs()
    else:
        cmd = ALLOWED_ACTIONS[action]
        ok, msg = run_cmd(cmd)

    status = 'success' if ok else 'error'
    cmd_str = ' '.join(ALLOWED_ACTIONS.get(action) or [action])
    save_log(sb, task_id, status, msg, cmd_str)

    # Actualizar last_run
    sb.table('cron_nexus').update({
        'last_run': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }).eq('id', task_id).execute()

    log.info(f"{'✅' if ok else '❌'} [{name}] {status}: {msg[:100]}")

def main():
    if not lock():
        log.info("Worker ya corriendo — skip")
        return

    try:
        now = datetime.now(TZ)
        weekday = now.weekday()
        log.info(f"=== CRON WORKER {now.strftime('%d/%m/%Y %H:%M')} ===")

        sb = get_sb()
        tasks = sb.table('cron_nexus').select('*').eq('active', True).order('priority').execute().data

        if not tasks:
            log.info("Sin tareas activas")
            return

        for task in tasks:
            run, reason = should_run(task, now, weekday)
            if not run:
                continue
            execute_task(task, sb)

    except Exception as e:
        log.error(f"Error crítico worker: {e}")
    finally:
        unlock()

if __name__ == '__main__':
    main()
