#!/usr/bin/env python3
"""Alertas Telegram adicionales para CitasFlash"""
import os, requests, json, subprocess
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
load_dotenv('/root/.env.citafast')

sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT  = os.getenv('TELEGRAM_CHAT_ID')

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id":CHAT,"text":msg,"parse_mode":"Markdown"}, timeout=10)
    except: pass

def check():
    cuentas = sb.table("cuentas_citafast").select("*").execute().data or []
    activas = [c for c in cuentas if c.get('is_active')]
    
    # Alerta: login fail
    for c in cuentas:
        if c.get('last_login_fail'):
            tg(f"🔒 *Login Fail*\n📧 {c['email']}\n👤 {c.get('nombre','—')}\n🕐 Revisar credenciales")
    
    # Alerta: bloqueada AIS — solo 1 vez cada 60 min
    import os, json as _json
    CACHE_FILE = '/tmp/nexus_alertas_cache.json'
    try:
        cache = _json.load(open(CACHE_FILE)) if os.path.exists(CACHE_FILE) else {}
    except: cache = {}
    
    now_ts = datetime.now().timestamp()
    for c in cuentas:
        if 'Bloqueada' in (c.get('status') or ''):
            key = f"bloq_{c['email']}"
            last = cache.get(key, 0)
            if now_ts - last >= 3600:  # 60 minutos
                tg(f"⛔ *Bloqueada AIS*\n📧 {c['email']}\n👤 {c.get('nombre','—')}\n🕐 Pausada 1 hora")
                cache[key] = now_ts
    
    try:
        _json.dump(cache, open(CACHE_FILE,'w'))
    except: pass
    
    # Alerta: bot caído
    try:
        r = subprocess.run(['systemctl','is-active','nexus'],capture_output=True,text=True)
        if 'active' not in r.stdout:
            tg("🆘 *Bot CAÍDO*\nNexus no está activo\n🕐 "+datetime.now().strftime("%H:%M"))
    except: pass

check()
