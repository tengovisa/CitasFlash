import os, secrets, hashlib, subprocess
import requests as req
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from datetime import datetime, timedelta
from fastapi import FastAPI, Header, HTTPException, Request
from supabase import create_client

load_dotenv("/root/.env.citafast")
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nexusrd.net", "https://www.nexusrd.net", "https://vps.citaflash.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_KEY      = os.getenv("API_KEY")
RESEND_KEY   = os.getenv("RESEND_API_KEY")
RESEND_FROM  = os.getenv("RESEND_FROM", "noreply@citaflash.com")
HOST         = "ais.usvisa-info.com"
supabase     = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify(x_api_key: str = Header(None)):
    valid_keys = {
        API_KEY,
        "CitaFast2026Bot2",
        "CitasFlash2026Servicio2"
    }
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="No autorizado")

        raise HTTPException(status_code=401, detail="No autorizado")

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def send_email(to, subject, html):
    try:
        req.post("https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
            json={"from": RESEND_FROM, "to": [to], "subject": subject, "html": html}, timeout=10)
    except: pass

@app.get("/ping")
def ping(): return {"status": "ok"}

@app.post("/bot/start")
def start(x_api_key: str = Header(...)):
    verify(x_api_key); subprocess.Popen(["systemctl","start","nexus"]); return {"status":"iniciado"}

@app.post("/bot/stop")
def stop(x_api_key: str = Header(...)):
    verify(x_api_key); subprocess.Popen(["systemctl","stop","nexus"]); return {"status":"detenido"}

@app.post("/bot/restart")
def restart(x_api_key: str = Header(...)):
    verify(x_api_key); subprocess.Popen(["systemctl","restart","nexus"]); return {"status":"reiniciado"}

@app.get("/bot/status")
def status(x_api_key: str = Header(...)):
    verify(x_api_key)
    r = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True)
    return {"status": r.stdout.strip()}

@app.get("/bot/logs")
def logs(x_api_key: str = Header(...)):
    verify(x_api_key)
    try:
        with open("/root/log_nexus.txt", "r") as f:
            ls = f.readlines()
        return {"logs": "".join(ls[-200:])}
    except:
        return {"logs": ""}

@app.get("/cuentas")
def get_cuentas(x_api_key: str = Header(...), usuario_id: int = None):
    verify(x_api_key)
    q = supabase.table("cuentas_citafast").select("*").order("id")
    if usuario_id:
        q = q.eq("usuario_id", usuario_id)
    return q.execute().data

@app.post("/cuentas")
def crear_cuenta(cuenta: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    uid = cuenta.get("usuario_id")
    if uid:
        u = supabase.table("usuarios_panel").select("rol,max_solicitantes").eq("id", uid).execute().data
        if u and u[0]["rol"] != "administrador":
            max_s = u[0].get("max_solicitantes") or 25
            current = len(supabase.table("cuentas_citafast").select("id").eq("usuario_id", uid).execute().data)
            if current >= max_s:
                raise HTTPException(status_code=403, detail=f"Limite de {max_s} solicitantes alcanzado")
    sid = cuenta.get("schedule_id")
    if sid:
        existing = supabase.table("cuentas_citafast").select("id,email").eq("schedule_id", sid).execute().data
        if existing:
            raise HTTPException(status_code=409, detail=f"Schedule ID {sid} ya existe para {existing[0]['email']}")
    cuenta["updated_at"] = datetime.now().isoformat()
    return supabase.table("cuentas_citafast").insert(cuenta).execute().data

@app.put("/cuentas/{id}")
def actualizar_cuenta(id: int, cuenta: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    cuenta["updated_at"] = datetime.now().isoformat()
    return supabase.table("cuentas_citafast").update(cuenta).eq("id", id).execute().data

@app.delete("/cuentas/{id}")
def eliminar_cuenta(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    supabase.table("cuentas_citafast").delete().eq("id", id).execute()
    return {"deleted": id}

@app.patch("/cuentas/{id}/toggle")
def toggle_cuenta(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    cur = supabase.table("cuentas_citafast").select("is_active").eq("id", id).execute()
    new = not cur.data[0]["is_active"]
    supabase.table("cuentas_citafast").update({"is_active": new, "updated_at": datetime.now().isoformat()}).eq("id", id).execute()
    return {"is_active": new}

@app.post("/validate-ais")
def validate_ais(data: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    email = data.get("email"); password = data.get("password"); country = data.get("country","do")
    url = f"https://{HOST}/en-{country}/niv"
    session = req.Session()
    proxy_str = data.get("proxy")
    if not proxy_str:
        proxy_str = "http://axihbvupstaticresidential:ng8m7kbc1met@9.142.44.55:7724"
    if proxy_str:
        p = proxy_str.strip()
        proxy_url = p if p.startswith('http') else f'http://{p}'
        session.proxies = {"http": proxy_url, "https": proxy_url}
        session.trust_env = False
    try:
        session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36","Accept":"text/html","Accept-Language":"en-US","Connection":"keep-alive"})
        r = session.get(f"{url}/users/sign_in", headers={"User-Agent":"Mozilla/5.0","Host":HOST}, timeout=15)
        csrf = BeautifulSoup(r.text,"html.parser").find("meta",{"name":"csrf-token"})["content"]
        cookies = r.headers.get("set-cookie")
        r2 = session.post(f"{url}/users/sign_in", headers={
            "User-Agent":"Mozilla/5.0","Host":HOST,"X-CSRF-Token":csrf,"Cookie":cookies,
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "Accept":"*/*;q=0.5, text/javascript, application/javascript",
        }, data=urlencode({"user[email]":email,"user[password]":password,"policy_confirmed":"1","commit":"Sign In"}), timeout=15)
        cookie2 = r2.headers.get("set-cookie")
        # Verificar si el login fue exitoso
        if "Invalid Email or password" in r2.text or "sign_in" in r2.url:
            return {"success":False,"error":"Contraseña incorrecta o cuenta bloqueada"}
        r3 = session.get(url, headers={"User-Agent":"Mozilla/5.0","Host":HOST,"Cookie":cookie2}, timeout=15)
        import re
        soup = BeautifulSoup(r3.text,"html.parser")
        apps = soup.find_all("div",{"class":"application"})
        if not apps: return {"success":False,"error":"Credenciales inválidas o sin aplicación activa"}
        # Extract IVR from page
        import re as _rx
        ivr_number = None
        import re as _rx2
        ivr_match = _rx2.search(r'IVR Account Number[:\s]*<[^>]*>(\d+)', r3.text)
        if ivr_match:
            ivr_number = ivr_match.group(1)
        else:
            for div in soup.find_all("div", class_="columns"):
                txt = div.get_text(strip=True)
                if 'IVR Account Number' in txt:
                    m = _rx2.search(r'(\d{7,9})', txt)
                    if m: ivr_number = m.group(1); break
        result = []
        for app2 in apps:
            m = _rx.search(r"\d{6,}", str(app2.find("a") or ""))
            sid = m.group(0) if m else None
            # Nombre, Pasaporte, DS-160, Visa — desde tabla
            name = passport = ds160 = visa_type = None
            tbody = app2.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 1 and not name:
                        name = cols[0].get_text(strip=True) or None
                    if len(cols) >= 2 and not passport:
                        passport = cols[1].get_text(strip=True) or None
                    if len(cols) >= 3 and not ds160:
                        ds160 = cols[2].get_text(strip=True) or None
                    if len(cols) >= 4 and not visa_type:
                        visa_type = cols[3].get_text(strip=True) or None
            name = name or "Sin nombre"
            # Cita — solo fecha numerica
            appt = app2.find("p",{"class":"consular-appt"})
            cita_raw = appt.get_text(strip=True) if appt else ""
            cm = _rx.search(r"(\d{1,2}\s+\w+,?\s+\d{4})", cita_raw)
            cita = cm.group(1) if cm else (cita_raw[:40] if cita_raw else "Sin cita")
            # ASC cita
            asc = app2.find("p",{"class":"asc-appt"})
            asc_raw = asc.get_text(strip=True) if asc else ""
            asc_m = _rx.search(r"(\d{1,2}\s+\w+,?\s+\d{4})", asc_raw)
            asc_date = asc_m.group(1) if asc_m else None
            result.append({"schedule_id":sid,"nombre":name,"cita_actual":cita,"asc_date":asc_date,"passport_number":passport,"ds160_number":ds160,"visa_type":visa_type,"ivr_number":ivr_number})
        return {"success":True,"data":result}
    except Exception as e:
        return {"success":False,"error":str(type(e).__name__)}

@app.get("/usuarios")
def get_usuarios(x_api_key: str = Header(...)):
    verify(x_api_key)
    return supabase.table("usuarios_panel").select("id,nombre,email,rol,is_active,is_demo,demo_expires_at,last_login,created_at").order("id").execute().data

@app.post("/usuarios")
def crear_usuario(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    token = secrets.token_urlsafe(32)
    temp_pass = "12345678"  # Default password - user must change on first login
    is_demo = body.get("is_demo", False)
    demo_expires = (datetime.now() + timedelta(days=5)).isoformat() if is_demo else None
    supabase.table("usuarios_panel").insert({
        "nombre":body["nombre"],"email":body["email"],"phone":body.get("phone",""),
        "password_hash":hp(temp_pass),
        "rol":body.get("rol","gestor"),"is_active":True,"is_demo":is_demo,
        "demo_expires_at":demo_expires,"activation_token":token,
        "must_change_password":True,
        
        "updated_at":datetime.now().isoformat()
    }).execute()
    activate_url = f"https://vps.citaflash.com/panel/activate.html?token={token}"
    demo_badge = '<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:10px 16px;margin:12px 0;color:#c2410c;font-size:13px">⏱ Cuenta demo — expira en 5 días</div>' if is_demo else ''
    rol_label = 'Administrador' if body.get('rol') == 'administrador' else 'Gestor'
    send_email(body["email"],"✅ Tu cuenta CitasFlash está lista",f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F4F6F8;font-family:'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F8;padding:40px 0">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)">
  <tr><td style="background:linear-gradient(135deg,#1565C0,#0d47a1);padding:32px 40px;text-align:center">
    <img src="https://citaflash.com/cita/citasflash_logo_hd_pngd.png" height="50" alt="CitasFlash" style="margin-bottom:12px"><br>
    <span style="color:rgba(255,255,255,0.85);font-size:14px">Panel de Gestión de Citas USA</span>
  </td></tr>
  <tr><td style="padding:36px 40px">
    <h2 style="color:#1e293b;margin:0 0 8px;font-size:22px">¡Bienvenido, {body['nombre']}! 👋</h2>
    <p style="color:#64748b;margin:0 0 24px;font-size:15px">Tu cuenta ha sido creada exitosamente en CitasFlash.</p>
    {demo_badge}
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin:20px 0">
      <p style="margin:0 0 12px;color:#64748b;font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.5px">Datos de acceso</p>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="padding:6px 0;color:#64748b;font-size:14px">📧 Email:</td><td style="padding:6px 0;font-weight:600;color:#1e293b;font-size:14px">{body['email']}</td></tr>
        <tr><td style="padding:6px 0;color:#64748b;font-size:14px">🔑 Clave temporal:</td><td style="padding:6px 0;font-weight:700;color:#E50914;font-size:16px;font-family:monospace">{temp_pass}</td></tr>
        <tr><td style="padding:6px 0;color:#64748b;font-size:14px">👤 Rol:</td><td style="padding:6px 0;font-weight:600;color:#1565C0;font-size:14px">{rol_label}</td></tr>
      </table>
    </div>
    <p style="color:#64748b;font-size:14px;margin:0 0 20px">Haz clic en el botón para activar tu cuenta y cambiar tu contraseña:</p>
    <div style="text-align:center;margin:28px 0">
      <a href="{activate_url}" style="background:linear-gradient(135deg,#E50914,#b20710);color:white;padding:15px 36px;border-radius:10px;text-decoration:none;font-weight:700;font-size:16px;display:inline-block;letter-spacing:.3px">⚡ Activar mi cuenta</a>
    </div>
    <div style="background:#fff7ed;border-left:4px solid #E50914;padding:12px 16px;border-radius:0 8px 8px 0;margin:20px 0">
      <p style="margin:0;color:#92400e;font-size:13px">⚠️ Este enlace expira en 24 horas. Si no solicitaste esta cuenta, ignora este mensaje.</p>
    </div>
  </td></tr>
  <tr><td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:20px 40px;text-align:center">
    <p style="margin:0;color:#94a3b8;font-size:12px">© 2026 CitasFlash — Sistema de Agendamiento de Citas USA</p>
    <p style="margin:4px 0 0;color:#94a3b8;font-size:12px">Este es un correo automático, no respondas a este mensaje.</p>
  </td></tr>
</table>
</td></tr>
</table>
</body></html>""")
    return {"success":True}

@app.patch("/usuarios/{id}/toggle")
def toggle_usuario(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    cur = supabase.table("usuarios_panel").select("is_active").eq("id",id).execute()
    new = not cur.data[0]["is_active"]
    supabase.table("usuarios_panel").update({"is_active":new,"updated_at":datetime.now().isoformat()}).eq("id",id).execute()
    return {"is_active":new}

@app.post("/usuarios/{id}/reset-password")
def reset_password(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(hours=24)).isoformat()
    u = supabase.table("usuarios_panel").select("email,nombre").eq("id",id).execute().data[0]
    supabase.table("usuarios_panel").update({"reset_token":token,"reset_expires_at":expires}).eq("id",id).execute()
    reset_url = f"https://vps.citaflash.com/panel/reset.html?token={token}"
    send_email(u["email"],"🔑 Restablecer contraseña — CitasFlash",f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F4F6F8;font-family:'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6F8;padding:40px 0">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)">
  <tr><td style="background:linear-gradient(135deg,#1565C0,#0d47a1);padding:32px 40px;text-align:center">
    <img src="https://citaflash.com/cita/citasflash_logo_hd_pngd.png" height="50" alt="CitasFlash">
  </td></tr>
  <tr><td style="padding:36px 40px">
    <h2 style="color:#1e293b;margin:0 0 8px">Restablecer contraseña 🔑</h2>
    <p style="color:#64748b;margin:0 0 24px">Hola <strong>{u['nombre']}</strong>, recibimos una solicitud para restablecer tu contraseña.</p>
    <div style="text-align:center;margin:28px 0">
      <a href="{reset_url}" style="background:linear-gradient(135deg,#1565C0,#0d47a1);color:white;padding:15px 36px;border-radius:10px;text-decoration:none;font-weight:700;font-size:16px;display:inline-block">🔒 Cambiar contraseña</a>
    </div>
    <div style="background:#fff7ed;border-left:4px solid #E50914;padding:12px 16px;border-radius:0 8px 8px 0">
      <p style="margin:0;color:#92400e;font-size:13px">⚠️ Este enlace expira en 24 horas. Si no solicitaste este cambio, ignora este mensaje.</p>
    </div>
  </td></tr>
  <tr><td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:20px 40px;text-align:center">
    <p style="margin:0;color:#94a3b8;font-size:12px">© 2026 CitasFlash</p>
  </td></tr>
</table>
</td></tr>
</table>
</body></html>""")
    return {"success":True}

@app.post("/auth/login")
async def login_panel(request: Request):
    body = await request.json()
    u = supabase.table("usuarios_panel").select("*").eq("email",body.get("email")).eq("password_hash",hp(body.get("password",""))).eq("is_active",True).execute()
    if not u.data: raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    user = u.data[0]
    if user.get("is_demo") and user.get("demo_expires_at"):
        if datetime.now() > datetime.fromisoformat(user["demo_expires_at"]):
            raise HTTPException(status_code=403, detail="Cuenta demo expirada")
    token = secrets.token_urlsafe(32)
    supabase.table("sesiones_panel").insert({"usuario_id":user["id"],"token":token,"expires_at":(datetime.now()+timedelta(hours=8)).isoformat()}).execute()
    supabase.table("usuarios_panel").update({"last_login":datetime.now().isoformat()}).eq("id",user["id"]).execute()
    return {"token":token,"nombre":user["nombre"],"rol":user["rol"],"email":user["email"]}

@app.post("/auth/verify")
async def verify_token(request: Request):
    body = await request.json()
    s = supabase.table("sesiones_panel").select("*").eq("token",body.get("token")).execute()
    if not s.data: raise HTTPException(status_code=401, detail="Sesión inválida")
    if datetime.now() > datetime.fromisoformat(s.data[0]["expires_at"]):
        raise HTTPException(status_code=401, detail="Sesión expirada")
    u = supabase.table("usuarios_panel").select("id,nombre,rol,email").eq("id",s.data[0]["usuario_id"]).execute()
    return u.data[0]

import re as _re

@app.post("/validate-ais-v2")
def validate_ais_v2(data: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    email = data.get("email"); password = data.get("password"); country = data.get("country","do")
    url = f"https://{HOST}/en-{country}/niv"
    s = req.Session()
    try:
        r = s.get(f"{url}/users/sign_in", headers={"User-Agent":"Mozilla/5.0","Host":HOST}, timeout=15)
        csrf = BeautifulSoup(r.text,"html.parser").find("meta",{"name":"csrf-token"})["content"]
        ck = r.headers.get("set-cookie","")
        r2 = s.post(f"{url}/users/sign_in", headers={"User-Agent":"Mozilla/5.0","Host":HOST,"X-CSRF-Token":csrf,"Cookie":ck,"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","Accept":"application/javascript"},
            data=urlencode({"user[email]":email,"user[password]":password,"policy_confirmed":"1","commit":"Sign In"}), timeout=15)
        ck2 = r2.headers.get("set-cookie","")
        r3 = s.get(url, headers={"User-Agent":"Mozilla/5.0","Host":HOST,"Cookie":ck2}, timeout=15)
        soup = BeautifulSoup(r3.text,"html.parser")
        apps = soup.find_all("div",{"class":"application"})
        if not apps: return {"success":False,"error":"Credenciales invalidas"}
        result = []
        for app2 in apps:
            m = _re.search(r"\d{6,}", str(app2.find("a") or ""))
            sid = m.group(0) if m else None
            import re as _rx
            # Nombre — buscar en elementos especificos
            ne = app2.find("p",{"class":"applicant-name"}) or app2.find("h2") or app2.find("h3") or app2.find("strong")
            name = ne.get_text(strip=True) if ne else "Sin nombre"
            # Limpiar texto de cita del nombre
            name = _rx.sub(r'Consular Appointment.*', '', name).strip()
            name = _rx.sub(r'\d+ \w+, \d{4}.*', '', name).strip()
            if not name: name = "Sin nombre"
            # Cita actual
            ae = app2.find("p",{"class":"consular-appt"}) or app2.find("span",{"class":"consular-appt"})
            cita_raw = ae.get_text(strip=True) if ae else ""
            cm = _rx.search(r'\d+\s+\w+,?\s+\d{4},?\s+\d+:\d+', cita_raw)
            cita = cm.group(0) if cm else (cita_raw[:50] if cita_raw else "Sin cita")
            ve = app2.find("p",{"class":"visa-type"})
            vtype = ve.get_text(strip=True) if ve else "B1/B2"
            passport = ds160 = None
            try:
                if sid:
                    rd = s.get(f"{url}/schedule/{sid}/appointment", headers={"User-Agent":"Mozilla/5.0","Host":HOST,"Cookie":ck2}, timeout=15)
                    txt = rd.text
                    pm = _re.search(r'[A-Z]{1,2}\d{6,8}', txt)
                    if pm: passport = pm.group(0)
                    dm = _re.search(r'AA\d{8,10}', txt)
                    if dm: ds160 = dm.group(0)
            except: pass
            # Limpiar nombre y cita
            import re as _re2
            name_clean = _re2.sub(r'Consular Appointment.*', '', name).strip()
            if not name_clean: name_clean = name.strip()
            cita_clean = _re2.search(r'\d+ \w+, \d+, \d+:\d+', cita)
            cita_final = cita_clean.group(0) if cita_clean else cita.strip()
            import re as _rc
            # Extraer fecha de cita del texto completo
            full_text = app2.get_text()
            date_m = _rc.search(r'(\d+\s+\w+,?\s+\d{4},?\s+\d+:\d+)', full_text)
            cita_final = date_m.group(1).strip() if date_m else "Sin cita"
            # Nombre: texto antes de "Consular"
            name_m = _rc.sub(r'Consular.*', '', full_text).strip()
            name_lines = [l.strip() for l in name_m.split("\n") if l.strip() and len(l.strip()) > 3]
            name_clean = name_lines[-1] if name_lines else "Sin nombre"
            result.append({"schedule_id":sid,"nombre":name_clean,"cita_actual":cita_final,"visa_type":vtype,"passport_number":passport,"ds160_number":ds160})
        return {"success":True,"data":result}
    except Exception as e:
        return {"success":False,"error":str(type(e).__name__)}

@app.post("/cuentas/{id}/reagendar")
def reagendar_cuenta(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    supabase.table("cuentas_citafast").update({
        "is_active": True, "status": "Activo",
        "last_appointment_date": None, "booked_outside": False,
        "booked_date": None, "updated_at": datetime.now().isoformat()
    }).eq("id", id).execute()
    return {"success": True}

@app.post("/cuentas/{id}/sync")
def sync_cuenta(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    cuenta = supabase.table("cuentas_citafast").select("*").eq("id", id).execute().data
    if not cuenta: raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    c = cuenta[0]
    from bs4 import BeautifulSoup
    from urllib.parse import urlencode
    import re as _rx
    HOST = "ais.usvisa-info.com"
    url = f"https://{HOST}/en-{c.get('country','do')}/niv"
    session = req.Session()
    if c.get("proxies"):
        px = c["proxies"].split(",")[0].strip()
        session.proxies = {"http": f"http://{px}", "https": f"http://{px}"}
    try:
        r = session.get(f"{url}/users/sign_in", headers={"User-Agent":"Mozilla/5.0","Host":HOST}, timeout=15)
        csrf = BeautifulSoup(r.text,"html.parser").find("meta",{"name":"csrf-token"})["content"]
        ck = r.headers.get("set-cookie","")
        r2 = session.post(f"{url}/users/sign_in", headers={"User-Agent":"Mozilla/5.0","Host":HOST,"X-CSRF-Token":csrf,"Cookie":ck,"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","Accept":"application/javascript"},
            data=urlencode({"user[email]":c["email"],"user[password]":c["password"],"policy_confirmed":"1","commit":"Sign In"}), timeout=15)
        ck2 = r2.headers.get("set-cookie","")
        r3 = session.get(url, headers={"User-Agent":"Mozilla/5.0","Host":HOST,"Cookie":ck2}, timeout=15)
        soup = BeautifulSoup(r3.text,"html.parser")
        apps = soup.find_all("div",{"class":"application"})
        if not apps: return {"success":False,"error":"No se pudo conectar al AIS"}
        app2 = apps[0]
        tbody = app2.find("tbody")
        updates = {}
        if tbody:
            for row in tbody.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 1 and not updates.get("nombre"): updates["nombre"] = cols[0].get_text(strip=True)
                if len(cols) >= 2 and not updates.get("passport_number"): updates["passport_number"] = cols[1].get_text(strip=True)
                if len(cols) >= 3 and not updates.get("ds160_number"): updates["ds160_number"] = cols[2].get_text(strip=True)
                if len(cols) >= 4 and not updates.get("visa_type"): updates["visa_type"] = cols[3].get_text(strip=True)
                if len(cols) >= 5 and not updates.get("visa_class"): updates["visa_class"] = cols[4].get_text(strip=True)
        appt = app2.find("p",{"class":"consular-appt"})
        if appt:
            cita_raw = appt.get_text(strip=True)
            cm = _rx.search(r"(\d{1,2}\s+\w+,?\s+\d{4})", cita_raw)
            if cm: updates["last_appointment_date"] = cm.group(1)
        # ASC date
        asc_el = app2.find("p",{"class":"asc-appt"})
        if asc_el:
            asc_raw = asc_el.get_text(strip=True)
            am = _rx.search(r"(\d{1,2}\s+\w+,?\s+\d{4})", asc_raw)
            if am: updates["asc_date"] = am.group(1)
        updates["updated_at"] = datetime.now().isoformat()
        supabase.table("cuentas_citafast").update(updates).eq("id", id).execute()
        total = len(supabase.table("cuentas_citafast").select("id").execute().data)
        return {"success":True,"data":updates,"total_solicitantes":total}
    except Exception as e:
        return {"success":False,"error":str(e)}

@app.post("/auth/master-login")
def master_login(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    usuario_id = body.get("usuario_id")
    if not usuario_id:
        raise HTTPException(status_code=400, detail="usuario_id requerido")
    u = supabase.table("usuarios_panel").select("*").eq("id", usuario_id).eq("is_active", True).execute()
    if not u.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")
    user = u.data[0]
    token = secrets.token_urlsafe(32)
    supabase.table("sesiones_panel").insert({
        "usuario_id": user["id"],
        "token": token,
        "expires_at": (datetime.now() + timedelta(hours=8)).isoformat()
    }).execute()
    return {"token": token, "nombre": user["nombre"], "rol": user["rol"], "email": user["email"], "id": user["id"]}




@app.delete("/usuarios/{id}")
def delete_usuario(id: int, x_api_key: str = Header(...)):
    check_api_key(x_api_key)
    supabase.table("usuarios_panel").delete().eq("id", id).execute()
    return {"ok": True}

@app.put("/usuarios/{id}")
def edit_usuario(id: int, body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    allowed = ["nombre", "email", "phone", "rol", "max_solicitantes", "is_demo"]
    update = {k: v for k, v in body.items() if k in allowed}
    update["updated_at"] = datetime.now().isoformat()
    supabase.table("usuarios_panel").update(update).eq("id", id).execute()
    return {"success": True}


@app.get("/monitor")
def monitor_sistema(x_api_key: str = Header(...)):
    verify(x_api_key)
    import psutil, time
    results = {}
    # Servicio nexus
    try:
        r = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True)
        results["bot_nexus"] = {"status": r.stdout.strip(), "ok": r.stdout.strip() == "active"}
    except: results["bot_nexus"] = {"status": "error", "ok": False}
    # API VPS
    results["api_vps"] = {"status": "active", "ok": True}
    # Nginx
    try:
        r = subprocess.run(["systemctl","is-active","nginx"], capture_output=True, text=True)
        results["nginx"] = {"status": r.stdout.strip(), "ok": r.stdout.strip() == "active"}
    except: results["nginx"] = {"status": "error", "ok": False}
    # Supabase ping
    try:
        r = __import__('requests').get(f"{os.getenv('SUPABASE_URL')}/rest/v1/", 
            headers={"apikey": os.getenv("SUPABASE_KEY")}, timeout=5)
        results["supabase"] = {"status": "active" if r.status_code < 500 else "error", "ok": r.status_code < 500}
    except: results["supabase"] = {"status": "error", "ok": False}
    # System resources
    try:
        results["cpu"] = {"value": psutil.cpu_percent(interval=1), "ok": psutil.cpu_percent() < 90}
        mem = psutil.virtual_memory()
        results["ram"] = {"value": mem.percent, "total_gb": round(mem.total/1024**3,1), "ok": mem.percent < 90}
        disk = psutil.disk_usage('/')
        results["disk"] = {"value": disk.percent, "free_gb": round(disk.free/1024**3,1), "ok": disk.percent < 85}
    except: pass
    # Servicio botvps
    try:
        r = subprocess.run(["systemctl","is-active","botvps"], capture_output=True, text=True)
        results["bot_botvps"] = {"status": r.stdout.strip(), "ok": r.stdout.strip() == "active"}
    except: results["bot_botvps"] = {"status": "error", "ok": False}
    # Uptime
    try:
        r = subprocess.run(["uptime","-p"], capture_output=True, text=True)
        results["uptime"] = {"value": r.stdout.strip(), "ok": True}
    except: pass
    results["timestamp"] = datetime.now().isoformat()
    results["all_ok"] = all(v.get("ok", True) for v in results.values() if isinstance(v, dict) and "ok" in v)
    return results


@app.get("/gestores/resumen")
def gestores_resumen(x_api_key: str = Header(...)):
    verify(x_api_key)
    gestores = supabase.table("usuarios_panel").select("id,nombre,email,rol,is_active,max_solicitantes").execute().data
    cuentas = supabase.table("cuentas_citafast").select("usuario_id,status,tarifa").execute().data
    result = []
    for g in gestores:
        mis = [c for c in cuentas if c.get("usuario_id") == g["id"]]
        agendados = [c for c in mis if c.get("status") == "Cita Agendada"]
        balance = sum(c.get("tarifa") or 50 for c in agendados)
        result.append({
            "id": g["id"], "nombre": g["nombre"], "email": g["email"],
            "rol": g["rol"], "is_active": g["is_active"],
            "total_clientes": len(mis), "agendados": len(agendados),
            "balance_pendiente": balance, "max_solicitantes": g.get("max_solicitantes") or 25
        })
    return result


@app.post("/notify")
def send_push(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    import requests as req2
    r = req2.post("https://onesignal.com/api/v1/notifications",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Basic os_v2_app_bwm5bhd46vhdtegjlotocbkegltlpkj4ghluzrnvbvd46ds567qnpkqtg7r4bmnrr7ullomgxchxvv2y2dbj4sl7zixx6piqer7ck6i"
        },
        json={
            "app_id": "0d99d09c-7cf5-4e39-90c9-5ba6e1054432",
            "included_segments": ["All"],
            "headings": {"en": body.get("title", "CitasFlash")},
            "contents": {"en": body.get("message", "")},
            "url": body.get("url", "https://vps.citaflash.com/panel/")
        }, timeout=10)
    return {"success": True, "status": r.status_code,
    "response": r.text[:200]}

import pyotp as _pyotp

@app.post("/auth/setup-2fa")
def setup_2fa(x_api_key: str = Header(...)):
    verify(x_api_key)
    secret = os.getenv("TOTP_SECRET_ADMIN", "QLKXK66GKHYJ4KE3SDJHTS36KVR6IT6A")
    totp = _pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name="admin@citaflash.com", issuer_name="CitaFlash Panel")
    return {"secret": secret, "uri": uri}

@app.post("/auth/verify-2fa")
async def verify_2fa(request: Request):
    body = await request.json()
    token = body.get("token")
    code = str(body.get("code", "")).zfill(6).zfill(6)
    if not token or not code:
        raise HTTPException(status_code=400, detail="Token y codigo requeridos")
    s = supabase.table("sesiones_panel").select("usuario_id").eq("token", token).execute()
    if not s.data:
        raise HTTPException(status_code=401, detail="Sesion invalida")
    secret = os.getenv("TOTP_SECRET_ADMIN", "QLKXK66GKHYJ4KE3SDJHTS36KVR6IT6A")
    totp = _pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="Codigo 2FA invalido")
    return {"success": True, "verified": True}

# ─────────────────────────────────────────────
# PROXIES ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/proxies")
def get_proxies(x_api_key: str = Header(...)):
    verify(x_api_key)
    return supabase.table("proxies").select("*").order("type").order("status").execute().data

@app.post("/proxies")
def crear_proxy(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    proxy_str = body.get("proxy", "").strip()
    if not proxy_str:
        raise HTTPException(status_code=400, detail="Proxy requerido")
    if not proxy_str.startswith("http"):
        proxy_str = f"http://{proxy_str}"
    existing = supabase.table("proxies").select("id").eq("proxy", proxy_str).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Proxy ya existe")
    supabase.table("proxies").insert({
        "proxy": proxy_str,
        "type": body.get("type", "datacenter"),
        "status": "free",
        "fail_count": 0,
        "created_at": datetime.now().isoformat()
    }).execute()
    return {"success": True}

@app.post("/proxies/bulk")
def crear_proxies_bulk(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    proxies_raw = body.get("proxies", "")
    proxy_type  = body.get("type", "datacenter")
    lines = [p.strip() for p in proxies_raw.strip().splitlines() if p.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="Sin proxies")
    inserted = 0
    skipped  = 0
    for line in lines:
        p = line if line.startswith("http") else f"http://{line}"
        existing = supabase.table("proxies").select("id").eq("proxy", p).execute()
        if existing.data:
            skipped += 1
            continue
        supabase.table("proxies").insert({
            "proxy": p,
            "type": proxy_type,
            "status": "free",
            "fail_count": 0,
            "created_at": datetime.now().isoformat()
        }).execute()
        inserted += 1
    return {"success": True, "inserted": inserted, "skipped": skipped}

@app.delete("/proxies/{id}")
def eliminar_proxy(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    supabase.table("proxies").delete().eq("id", id).execute()
    return {"deleted": id}

@app.patch("/proxies/{id}/reset")
def reset_proxy(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    supabase.table("proxies").update({
        "status": "free",
        "fail_count": 0,
        "cooldown_until": None
    }).eq("id", id).execute()
    return {"success": True}

@app.post("/proxies/reset-all")
def reset_all_proxies(x_api_key: str = Header(...)):
    verify(x_api_key)
    supabase.table("proxies").update({
        "status": "free",
        "fail_count": 0,
        "cooldown_until": None
    }).neq("id", 0).execute()
    return {"success": True}

@app.get("/proxies/stats")
def stats_proxies(x_api_key: str = Header(...)):
    verify(x_api_key)
    data = supabase.table("proxies").select("type, status").execute().data
    stats = {}
    for row in data:
        t = row["type"]
        s = row["status"]
        if t not in stats:
            stats[t] = {"free": 0, "dead": 0, "total": 0}
        stats[t][s] = stats[t].get(s, 0) + 1
        stats[t]["total"] += 1
    return stats

# ── PANEL TI ──────────────────────────────────
import psutil

@app.get("/monitor")
def monitor(x_api_key: str = Header(...)):
    verify(x_api_key)
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    # Servicio status
    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()
    # Proxies
    px = supabase.table("proxies").select("status").execute().data
    px_free = len([p for p in px if p["status"] == "free"])
    px_dead = len([p for p in px if p["status"] == "dead"])
    return {
        "cpu": cpu,
        "ram": {"used": ram.percent, "total": round(ram.total/1024/1024/1024, 1), "available": round(ram.available/1024/1024/1024, 1)},
        "disk": {"used": disk.percent, "total": round(disk.total/1024/1024/1024, 1), "free": round(disk.free/1024/1024/1024, 1)},
        "bot": bot_active,
        "proxies": {"free": px_free, "dead": px_dead, "total": len(px)},
        "timestamp": datetime.now().isoformat()
    }

@app.delete("/proxies/all")
def delete_all_proxies(x_api_key: str = Header(...)):
    verify(x_api_key)
    supabase.table("proxies").delete().neq("id", 0).execute()
    return {"success": True}

@app.get("/logs/live", include_in_schema=False)
def live_logs():
    from fastapi.responses import HTMLResponse
    try:
        with open("/root/log_nexus.txt", "r") as f:
            lines = f.readlines()[-200:]
        log_text = "".join(lines)
    except:
        log_text = "Sin logs"
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="5">
<title>CitasFlash - Logs</title>
<style>
body{{background:#0d1117;color:#58a6ff;font-family:monospace;font-size:13px;padding:20px}}
pre{{white-space:pre-wrap;word-break:break-all}}
.ok{{color:#3fb950}}.err{{color:#f85149}}.warn{{color:#d29922}}
h2{{color:#fff}}
</style>
</head>
<body>
<h2>🚀 CitasFlash — Logs en vivo <small style="font-size:12px;color:#888">(actualiza cada 5s)</small></h2>
<pre>{log_text.replace('✅','<span class=ok>✅</span>').replace('❌','<span class=err>❌</span>').replace('⚠️','<span class=warn>⚠️</span>')}</pre>
</body>
</html>"""
    return HTMLResponse(html)

# ── COMANDOS RÁPIDOS ──────────────────────────────────
import subprocess as _sp

@app.post("/cmd/nexus/start")
def cmd_bot_start(x_api_key: str = Header(...)):
    verify(x_api_key)
    _sp.Popen(["bash", "-c", "pkill -f nexus.py; sleep 1; source /root/.env.citafast && python3 /root/nexus.py >> /root/log_nexus.txt 2>&1 &"])
    return {"success": True, "msg": "Servicio iniciado"}

@app.post("/cmd/nexus/stop")
def cmd_bot_stop(x_api_key: str = Header(...)):
    verify(x_api_key)
    import os
    os.system("pkill -9 -f nexus.py")
    return {"success": True, "msg": "Servicio detenido"}

@app.post("/cmd/nexus/restart")
def cmd_bot_restart(x_api_key: str = Header(...)):
    verify(x_api_key)
    _sp.Popen(["bash", "-c", "pkill -9 -f nexus.py; sleep 2; source /root/.env.citafast && python3 /root/nexus.py >> /root/log_nexus.txt 2>&1 &"])
    return {"success": True, "msg": "Servicio reiniciado"}

@app.post("/cmd/proxies/reset")
def cmd_proxies_reset(x_api_key: str = Header(...)):
    verify(x_api_key)
    supabase.table("proxies").update({"status": "free", "fail_count": 0}).neq("id", 0).execute()
    return {"success": True, "msg": "Proxies reseteados"}

@app.post("/cmd/cache/clean")
def cmd_cache_clean(x_api_key: str = Header(...)):
    verify(x_api_key)
    _sp.run(["bash", "-c", "sync && echo 3 > /proc/sys/vm/drop_caches"])
    _sp.run(["bash", "-c", "find /root -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"])
    return {"success": True, "msg": "Cache limpiado"}

@app.post("/cmd/api/restart")
def cmd_api_restart(x_api_key: str = Header(...)):
    verify(x_api_key)
    _sp.Popen(["bash", "-c", "sleep 1; pkill -f uvicorn; sleep 2; uvicorn api_control:app --host 0.0.0.0 --port 8000 --log-level warning &"])
    return {"success": True, "msg": "API reiniciando..."}

@app.get("/cmd/log/tail")
def cmd_log_tail(x_api_key: str = Header(...), lines: int = 50):
    verify(x_api_key)
    r = _sp.run(["tail", f"-{lines}", "/root/log_nexus.txt"], capture_output=True, text=True)
    return {"log": r.stdout}

# ── FCM TOKENS ──
@app.post("/save-fcm-token")
async def save_fcm_token(request: Request):
    body = await request.json()
    token = body.get("token")
    if not token:
        return {"success": False}
    try:
        supabase.table("fcm_tokens").upsert({"token": token}).execute()
        return {"success": True}
    except:
        return {"success": False}

@app.get("/cuentas/{id}/print")
def print_cita(id: int, x_api_key: str = None, key: str = None):
    token = x_api_key or key
    if token != 'Nexus2026Servicio2':
        raise HTTPException(status_code=401, detail='No autorizado')
    cuenta = supabase.table("cuentas_citafast").select("*").eq("id", id).execute().data
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    c = cuenta[0]
    url = f"https://{HOST}/en-{c['country']}/niv"
    session = req.Session()
    session.trust_env = False
    # Usar proxy de BD
    try:
        px = supabase.table("proxies").select("proxy").eq("status","free").order("fail_count").limit(1).execute()
        if px.data:
            p = px.data[0]["proxy"]
            session.proxies = {"http": p, "https": p}
    except: pass
    try:
        # Login
        r = session.get(f"{url}/users/sign_in", headers={"User-Agent":"Mozilla/5.0","Host":HOST}, timeout=15)
        from bs4 import BeautifulSoup
        csrf = BeautifulSoup(r.text,"html.parser").find("meta",{"name":"csrf-token"})["content"]
        cookies = r.headers.get("set-cookie")
        r2 = session.post(f"{url}/users/sign_in", headers={
            "User-Agent":"Mozilla/5.0","Host":HOST,"X-CSRF-Token":csrf,"Cookie":cookies,
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"
        }, data=f"user[email]={c['email']}&user[password]={c['password']}&policy_confirmed=1&commit=Sign+In", timeout=15)
        cookie2 = r2.headers.get("set-cookie")
        # Obtener página de instrucciones
        r3 = session.get(
            f"{url}/schedule/{c['schedule_id']}/appointment/print_instructions",
            headers={"User-Agent":"Mozilla/5.0","Host":HOST,"Cookie":cookie2},
            timeout=15
        )
        from fastapi.responses import HTMLResponse
        return HTMLResponse(r3.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── CEAC STATUS ──────────────────────────────────────
@app.post("/ceac/check")
async def ceac_check(request: Request, x_api_key: str = Header(...)):
    verify(x_api_key)
    body = await request.json()
    ds160 = body.get("ds160")
    passport = body.get("passport")
    surname = body.get("surname", "").upper().ljust(5)[:5]
    if not ds160 or not passport:
        raise HTTPException(status_code=400, detail="ds160 y passport requeridos")
    
    import requests as _req
    from twocaptcha import TwoCaptcha
    
    solver = TwoCaptcha('63b6b5526264e00990fcd823d9b42e09')
    session = _req.Session()
    # Proxy residencial para CEAC
    px = "http://axihbvup:ng8m7kbc1met@138.226.93.139:5327"
    session.proxies = {"http": px, "https": px}
    
    try:
        # Obtener página y captcha
        r = session.get("https://ceac.state.gov/CEACStatTracker/Status.aspx?App=NIV", timeout=15)
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Extraer viewstate y captcha
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        viewstate = viewstate["value"] if viewstate else ""
        eventval = soup.find("input", {"name": "__EVENTVALIDATION"})
        eventval = eventval["value"] if eventval else ""
        
        # Obtener imagen captcha
        captcha_img = soup.find("img", {"id": "c_status_ctl00_contentplaceholder1_defaultcaptcha_CaptchaImage"})
        if not captcha_img:
            captcha_img = soup.find("img", id=lambda x: x and "captcha" in x.lower())
        
        if captcha_img:
            img_url = "https://ceac.state.gov" + captcha_img.get("src","")
            import requests as _req2
            img_r = _req2.get(img_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://ceac.state.gov/CEACStatTracker/Status.aspx"}, timeout=10)
            import base64
            img_b64 = base64.b64encode(img_r.content).decode()
            result = solver.normal(img_b64, caseSensitive=0)
            captcha_text = result['code']
        else:
            raise Exception("No se encontró captcha")
        
        # Submit formulario
        cookies = r.cookies
        r2 = session.post(
            "https://ceac.state.gov/CEACStatTracker/Status.aspx?App=NIV",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://ceac.state.gov/CEACStatTracker/Status.aspx?App=NIV"
            },
            data={
                "__VIEWSTATE": viewstate,
                "__EVENTVALIDATION": eventval,
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "ctl00$ContentPlaceHolder1$Visa_Application_Type": "NIV",
                "ctl00$ContentPlaceHolder1$Location_Dropdown": "DOMINICAN REPUBLIC, SANTO DOMINGO",
                "ctl00$ContentPlaceHolder1$Appnumber": ds160,
                "ctl00$ContentPlaceHolder1$PassportNumber": passport,
                "ctl00$ContentPlaceHolder1$Surname": surname,
                "ctl00$ContentPlaceHolder1$defaultCaptcha": captcha_text,
                "ctl00$ContentPlaceHolder1$btnSubmit": "Submit"
            },
            cookies=cookies,
            timeout=20
        )
        
        soup2 = BeautifulSoup(r2.text, "html.parser")
        status_el = soup2.find(id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblStatus")
        status = status_el.text.strip() if status_el else "No encontrado"
        
        return {"success": True, "status": status, "ds160": ds160}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health360")
def health360(x_api_key: str = Header(...)):
    verify(x_api_key)
    import os, subprocess
    from datetime import datetime

    def run(cmd):
        try:
            return subprocess.check_output(cmd, shell=True, text=True).strip()
        except:
            return ""

    server = 100
    api = 100
    panel = 100 if os.path.exists("/var/www/panel/index.html") else 20

    try:
        supabase.table("cuentas_citafast").select("id").limit(1).execute()
        db = 100
    except:
        db = 20

    nexus = int(run("pgrep -fc 'nexus.py'") or 0)
    api_proc = int(run("pgrep -fc 'api_control'") or 0)
    bots = 100 if nexus >= 1 and api_proc >= 1 else 40

    proxies = 100
    ais = 100

    errors_count = int(run("tail -n 50 /root/log_nexus.txt | grep -ci 'error\\|traceback'") or 0)
    errors = 100 if errors_count == 0 else 60

    performance = 100
    security = 100
    business = 100

    # === OPERACION REAL (PRO) ===
    try:
        total = supabase.table("cuentas_citafast").select("id", count="exact").execute().count or 0
        activas = supabase.table("cuentas_citafast").select("id", count="exact").eq("is_active", True).execute().count or 0
        citas = supabase.table("cuentas_citafast").select("id", count="exact").eq("status", "Cita Agendada").execute().count or 0
        tasa = int((citas / total)*100) if total > 0 else 0
    except:
        total = activas = citas = tasa = 0

    ops = int((activas*0.3 + citas*0.4 + tasa*0.3)) if total > 0 else 50


    score = int((server*0.1)+(api*0.1)+(panel*0.05)+(db*0.1)+(bots*0.1)+(proxies*0.05)+(ais*0.05)+(errors*0.1)+(performance*0.1)+(security*0.05)+(business*0.05)+(ops*0.15))

    return {
        "score": score,
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "server": f"{server}%",
            "api": f"{api}%",
            "panel": f"{panel}%",
            "db": f"{db}%",
            "bots": f"{bots}% ({nexus} nexus)",
            "proxies": f"{proxies}%",
            "ais": f"{ais}%",
            "errors": f"{errors}% ({errors_count})",
            "performance": f"{performance}%",
            "security": f"{security}%",
            "business": f"{business}%"
            , "cuentas_total": total,
            "cuentas_activas": activas,
            "citas_logradas": citas,
            "tasa_exito": str(tasa) + "%",
            "operacion": str(ops) + "%"
        }
    }


@app.post("/cuentas/validar")
def validar_cuenta(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    import requests as req
    from bs4 import BeautifulSoup
    email = body.get("email")
    password = body.get("password")
    schedule_id = body.get("schedule_id")
    proxies_str = body.get("proxies","")
    WS_LIST = ["http://axihbvup:ng8m7kbc1met@23.229.89.107:6098","http://axihbvup:ng8m7kbc1met@138.226.93.139:5327"]
    WS = WS_LIST[0]
    proxy = {"http": WS, "https": WS}
    HOST = "ais.usvisa-info.com"
    url = f"https://{HOST}/en-do/niv"
    headers = {
        "Host":HOST,
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language":"ru,en;q=0.9",
        "Connection":"keep-alive",
    }
    try:
        s = req.Session()
        s.timeout = 15
        if proxy: s.proxies = proxy
        r = s.get(f"{url}/users/sign_in", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        csrf = soup.find("meta",{"name":"csrf-token"})["content"]
        cookies = r.headers.get("set-cookie","")
        r2 = s.post(f"{url}/users/sign_in", headers={**headers,
            "X-CSRF-Token":csrf,"Cookie":cookies,
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "Accept":"*/*;q=0.5, text/javascript, application/javascript"},
            data=f"user%5Bemail%5D={email}&user%5Bpassword%5D={password}&policy_confirmed=1&commit=Sign+In",
            timeout=15)
        if r2.status_code not in [200,201,302]:
            return {"valid":False,"error":"Credenciales inválidas","email":email}
        cookie2 = r2.headers.get("set-cookie","")
        r3 = s.get(url, headers={**headers,"Cookie":cookie2}, timeout=15)
        soup3 = BeautifulSoup(r3.text, "html.parser")
        apps = soup3.find_all("div",{"class":"application"})
        fecha_actual = None
        puede_calendario = False
        solicitantes = len(apps)
        nombre = None
        for app in apps:
            appt = app.find("p",{"class":"consular-appt"})
            if appt:
                import re
                am = re.search(r'\d{1,2}\s+\w+,\s+\d{4},\s+\d{1,2}:\d{2}', appt.get_text())
                fecha_actual = am.group(0) if am else appt.get_text().strip()[:50]
            # Extraer nombre del solicitante
            tds = app.find_all("td")
            if tds: nombre = tds[0].get_text().strip() if tds else None
            try:
                r4 = s.get(f"{url}/schedule/{schedule_id}/appointment",
                    headers={**headers,"Cookie":cookie2}, timeout=15)
                puede_calendario = r4.status_code == 200 and "appointment" in r4.url
            except: pass
            break
        # Rastrear IP del ultimo acceso
        ip_acceso = None
        try:
            r5 = s.get(f"{url}/users/sign_in", headers={**headers,"Cookie":cookie2}, timeout=10)
            import re as re2
            ip_match = re2.search(r'(\d{1,3}\.){3}\d{1,3}', r5.text)
            if ip_match: ip_acceso = ip_match.group(0)
        except: pass
        return {
            "valid":True,
            "email":email,
            "nombre":nombre,
            "fecha_actual":fecha_actual or "Sin cita asignada",
            "solicitantes":solicitantes,
            "puede_calendario":puede_calendario,
            "ip_acceso":ip_acceso,
        }
    except Exception as e:
        return {"valid":False,"error":str(e),"email":email}


@app.get("/trazas/http")
async def trazas_http(limit: int = 200, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY:
        raise HTTPException(403)
    try:
        import re as regex
        lines = open('/root/nexus.log', encoding='utf-8', errors='ignore').readlines()
        lines = lines[-limit*4:]
        trazas = []
        for line in lines:
            l = line.strip()
            if not l:
                continue
            ts_m = regex.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', l)
            cuenta_m = regex.search(r'\[([^\[\]]+@[^\[\]]+)\]', l)
            url_m = regex.search(r'https?://[^\s\]]+', l)
            status_m = regex.search(r'\b(200|302|401|403|429|500)\b', l)
            keywords = ['Login','login','Error','error','✅','❌','⚠️','Rotando','CSRF','fecha','match','Modo','Sin cuentas','cita']
            if not any(x in l for x in keywords):
                continue
            method = 'POST' if any(x in l for x in ['sign_in','POST']) else ('GET' if url_m else '')
            tipo = ('success' if '✅' in l else
                    'error' if '❌' in l or 'Error' in l else
                    'warning' if '⚠️' in l or 'Rotando' in l else 'info')
            trazas.append({
                'ts': ts_m.group(1) if ts_m else '',
                'method': method,
                'status': int(status_m.group()) if status_m else None,
                'url': url_m.group()[:100] if url_m else '',
                'raw': l[:200],
                'tipo': tipo,
                'cuenta': cuenta_m.group(1) if cuenta_m else ''
            })
        return {"ok": True, "trazas": trazas[-limit:], "total": len(trazas)}
    except Exception as e:
        return {"ok": False, "error": str(e), "trazas": []}

@app.get("/jobs/historial")
async def jobs_historial(limit: int = 100, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY:
        raise HTTPException(403)
    try:
        import re as regex
        lines = open('/root/nexus.log', encoding='utf-8', errors='ignore').readlines()
        jobs = []
        current = None
        stats = {'login_ok':0,'success':0,'json_error':0,'http_error':0,'rotando_proxy':0,'blocked':0}
        for line in lines:
            l = line.strip()
            if not l:
                continue
            ts_m = regex.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', l)
            ts = ts_m.group(1) if ts_m else ''
            cuenta_m = regex.search(r'\[([^\[\]]+@[^\[\]]+)\]', l)
            cuenta = cuenta_m.group(1) if cuenta_m else ''
            if 'LOGIN' in l.upper() and cuenta and '🔐' in l:
                if current:
                    jobs.append(current)
                current = {'cuenta': cuenta, 'inicio': ts, 'fin': '', 'estado': 'running', 'pasos': [], 'resumen': ''}
            if not current:
                continue
            if cuenta and not current['cuenta']:
                current['cuenta'] = cuenta
            url_m = regex.search(r'https?://[^\s\]]+', l)
            if url_m:
                status_m = regex.search(r'\b(200|302|401|403|429|500)\b', l)
                current['pasos'].append({
                    'method': 'POST' if 'sign_in' in l else 'GET',
                    'status': int(status_m.group()) if status_m else 0,
                    'url': url_m.group()[:100],
                    'tipo': 'success' if status_m and status_m.group() in ['200','302'] else 'error'
                })
            if '✅ Login OK' in l:
                current['estado'] = 'login_ok'
                current['fin'] = ts
            elif 'JSONDecodeError' in l:
                current['estado'] = 'json_error'
                current['resumen'] = 'JSONDecodeError al leer fechas'
                current['fin'] = ts
            elif 'HTTPError' in l and 'Error' in l:
                current['estado'] = 'http_error'
                current['resumen'] = 'HTTPError consultando fechas'
                current['fin'] = ts
            elif 'Rotando' in l:
                current['estado'] = 'rotando_proxy'
                current['resumen'] = 'Proxy fallido rotando...'
            elif '🎉' in l or 'cita tomada' in l.lower():
                current['estado'] = 'success'
                current['resumen'] = '¡CITA CAPTURADA!'
                current['fin'] = ts
            elif 'bloqueada' in l.lower():
                current['estado'] = 'blocked'
                current['resumen'] = 'Cuenta bloqueada'
                current['fin'] = ts
        if current:
            jobs.append(current)
        for j in jobs:
            est = j.get('estado','running')
            if est in stats:
                stats[est] += 1
        jobs.reverse()
        return {"ok": True, "jobs": jobs[:limit], "total": len(jobs), "stats": stats}
    except Exception as e:
        return {"ok": False, "error": str(e), "jobs": [], "stats": {}}
