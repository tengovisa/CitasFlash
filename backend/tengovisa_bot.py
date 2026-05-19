import requests, json, time, os
from datetime import datetime, timedelta, timezone

TOKEN = "8924027697:AAHw6FrBJo2vp6avPPyfw5jbhFt3EGieFSU"
CHAT_ID = "1193245321"
SUPA = "https://lbttnpcpqdjmpktuoegs.supabase.co"
SKEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxidHRucGNwcWRqbXBrdHVvZWdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2NjAyNDEsImV4cCI6MjA5MTIzNjI0MX0.GsuZUkJIOmOITdl0hATt_P603a7vaI01j72nzG94O60"
LAST_FILE = "/root/.tv_last_lead"

def send(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def get_last():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE) as f: return f.read().strip()
    return (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

def set_last(ts):
    with open(LAST_FILE, 'w') as f: f.write(ts)

def check():
    last = get_last()
    r = requests.get(
        f"{SUPA}/rest/v1/leads?created_at=gt.{last}&order=created_at.asc&select=nombre,whatsapp,origen,notas,created_at",
        headers={"apikey": SKEY, "Accept-Profile": "crm"}
    )
    leads = r.json()
    if not isinstance(leads, list) or not leads: return
    for l in leads:
        origen = l.get('origen','—')
        tag = '📅 Cita' if 'Cita' in origen else '💼 Asesor' if 'Asesor' in origen else '🧠 Evaluac' if 'Evaluac' in origen else '💝 Madres' if 'Madre' in origen else '📥 Lead'
        nombre = l.get('nombre','—')
        wa = l.get('whatsapp','—')
        notas = (l.get('notas','') or '')[:120]
        hora = l.get('created_at','')[:16].replace('T',' ')
        msg = (f"🔔 <b>NUEVO LEAD</b>\n"
               f"{tag}\n"
               f"👤 <b>{nombre}</b>\n"
               f"📱 {wa}\n"
               f"📝 {notas}\n"
               f"🕐 {hora}\n"
               f"─────────────────\n"
               f"<a href='https://wa.me/{wa.replace('+','').replace(' ','').replace('-','')}'>💬 Abrir WhatsApp</a>")
        send(msg)
    set_last(leads[-1]['created_at'])

if __name__ == '__main__':
    send("✅ <b>TengoVisa Bot activo</b>\nRecibirás alertas de nuevos leads aquí.")
    while True:
        try: check()
        except Exception as e: print(f"Error: {e}")
        time.sleep(300)
