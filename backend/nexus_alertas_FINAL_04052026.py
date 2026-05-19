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
    
    # Alerta: bloqueada AIS
    for c in cuentas:
        if 'Bloqueada' in (c.get('status') or ''):
            tg(f"⛔ *Bloqueada AIS*\n📧 {c['email']}\n👤 {c.get('nombre','—')}\n🕐 Pausada 1 hora")
    
    # Alerta: bot caído
    try:
        r = subprocess.run(['systemctl','is-active','nexus'],capture_output=True,text=True)
        if 'active' not in r.stdout:
            tg("🆘 *Bot CAÍDO*\nNexus no está activo\n🕐 "+datetime.now().strftime("%H:%M"))
    except: pass

check()
