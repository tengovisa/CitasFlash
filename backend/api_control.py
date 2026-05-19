import os, secrets, hashlib, subprocess
from pathlib import Path
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

# === RUNTIME PERSISTENCE PATCH ===
RUNTIME_ENV_FILE = "/root/.env.citafast"

def _rt_truthy(v):
    return str(v).strip().lower() in ("1","true","yes","on","si","sí")

def _runtime_defaults():
    return {
        "dry_run": _rt_truthy(os.getenv("DRY_RUN", "true")),
        "csrf_refresh_seconds": int(os.getenv("CSRF_REFRESH_SECONDS", "240") or 240),
        "session_relogin_seconds": int(os.getenv("SESSION_RELOGIN_SECONDS", "540") or 540),
        "empty_dates_backoff_max_seconds": int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15") or 15),
    }

def _runtime_load_persisted():
    cfg = _runtime_defaults()
    p = Path(RUNTIME_ENV_FILE)
    if not p.exists():
        return cfg
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k == "DRY_RUN":
            cfg["dry_run"] = _rt_truthy(v)
        elif k == "CSRF_REFRESH_SECONDS":
            cfg["csrf_refresh_seconds"] = int(v or 240)
        elif k == "SESSION_RELOGIN_SECONDS":
            cfg["session_relogin_seconds"] = int(v or 540)
        elif k == "EMPTY_DATES_BACKOFF_MAX_SECONDS":
            cfg["empty_dates_backoff_max_seconds"] = int(v or 15)
    return cfg

def _runtime_save_persisted(cfg):
    p = Path(RUNTIME_ENV_FILE)
    lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
    want = {
        "DRY_RUN": "true" if bool(cfg["dry_run"]) else "false",
        "CSRF_REFRESH_SECONDS": str(int(cfg["csrf_refresh_seconds"])),
        "SESSION_RELOGIN_SECONDS": str(int(cfg["session_relogin_seconds"])),
        "EMPTY_DATES_BACKOFF_MAX_SECONDS": str(int(cfg["empty_dates_backoff_max_seconds"])),
    }
    seen = set()
    out = []
    for raw in lines:
        if "=" in raw and not raw.lstrip().startswith("#"):
            k = raw.split("=", 1)[0].strip()
            if k in want:
                out.append(f"{k}={want[k]}")
                seen.add(k)
                continue
        out.append(raw)
    for k, v in want.items():
        if k not in seen:
            out.append(f"{k}={v}")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    os.environ["DRY_RUN"] = want["DRY_RUN"]
    os.environ["CSRF_REFRESH_SECONDS"] = want["CSRF_REFRESH_SECONDS"]
    os.environ["SESSION_RELOGIN_SECONDS"] = want["SESSION_RELOGIN_SECONDS"]
    os.environ["EMPTY_DATES_BACKOFF_MAX_SECONDS"] = want["EMPTY_DATES_BACKOFF_MAX_SECONDS"]
RESEND_KEY   = os.getenv("RESEND_API_KEY")
RESEND_FROM  = os.getenv("RESEND_FROM", "noreply@citaflash.com")
HOST         = "ais.usvisa-info.com"
supabase     = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify(x_api_key: str = Header(None)):
    valid_keys = {
        API_KEY,
        "CitaFast2026Bot2",
        "CitasFlash2026Servicio2",
        "Nexus2026Servicio2",
    }
    if not x_api_key or x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="No autorizado")



import re
from datetime import datetime

def normalize_expired_ais_blocks():
    rows = supabase.table("cuentas_citafast").select("id,status,is_active").limit(2000).execute().data or []
    now = datetime.now()
    pat = re.compile(r'bloqueada ais hasta (.+?)(?:\.|$)', re.I)
    fixed = 0

    for r in rows:
        st = (r.get("status") or "").strip()
        m = pat.search(st)
        if not m:
            continue

        raw = m.group(1).strip()
        dt = None
        for fmt in (
            "%d %B, %Y, %H:%M:%S AST",
            "%d %B, %Y, %H:%M:%S",
            "%d %b, %Y, %H:%M:%S AST",
            "%d %b, %Y, %H:%M:%S",
        ):
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except:
                pass

        if dt and dt <= now:
            supabase.table("cuentas_citafast").update({
                "status": "Pendiente de revalidación",
                "is_active": False,
                "updated_at": datetime.now().isoformat()
            }).eq("id", r["id"]).execute()
            fixed += 1

    return {"ok": True, "fixed": fixed, "checked": len(rows)}


def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def _truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def check_duplicate_identifiers(schedule_id=None, ivr_number=None, exclude_id=None):
    if schedule_id:
        q = supabase.table("cuentas_citafast").select("id,email,schedule_id,ivr_number").eq("schedule_id", schedule_id)
        if exclude_id is not None:
            q = q.neq("id", exclude_id)
        rows = q.execute().data or []
        if rows:
            return {"field": "schedule_id", "value": schedule_id, "existing": rows[0]}
    if ivr_number:
        q = supabase.table("cuentas_citafast").select("id,email,schedule_id,ivr_number").eq("ivr_number", ivr_number)
        if exclude_id is not None:
            q = q.neq("id", exclude_id)
        rows = q.execute().data or []
        if rows:
            return {"field": "ivr_number", "value": ivr_number, "existing": rows[0]}
    return None

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
    normalize_expired_ais_blocks()
    verify(x_api_key)
    q = supabase.table("cuentas_citafast").select("*").order("id")
    if usuario_id:
        q = q.eq("usuario_id", usuario_id)
    return q.execute().data

@app.post("/cuentas")
def crear_cuenta(cuenta: dict, x_api_key: str = Header(...)):
    verify(x_api_key)

    force_save = _truthy(cuenta.pop("force_save", False))
    skip_validation = _truthy(cuenta.pop("skip_validation", False))
    auto_validate = not (force_save or skip_validation)

    uid = cuenta.get("usuario_id")
    if uid:
        u = supabase.table("usuarios_panel").select("rol,max_solicitantes").eq("id", uid).execute().data
        if u and u[0]["rol"] != "administrador":
            max_s = u[0].get("max_solicitantes") or 25
            current = len(supabase.table("cuentas_citafast").select("id").eq("usuario_id", uid).execute().data)
            if current >= max_s:
                raise HTTPException(status_code=403, detail=f"Limite de {max_s} solicitantes alcanzado")

    if auto_validate and cuenta.get("email") and cuenta.get("password"):
        validation_result = validate_ais({
            "email": cuenta.get("email"),
            "password": cuenta.get("password"),
            "country": cuenta.get("country", "do"),
            "proxy": cuenta.get("proxy")
        }, x_api_key)

        if validation_result.get("success") and validation_result.get("data"):
            first = validation_result["data"][0]
            field_map = {
                "schedule_id": "schedule_id",
                "ivr_number": "ivr_number",
                "total_personas": "total_personas",
                "last_appointment_date": "cita_actual",
                "asc_date": "asc_date",
                "passport_number": "passport_number",
                "ds160_number": "ds160_number",
                "visa_type": "visa_type",
                "nombre": "nombre",
            }
            for dst, src in field_map.items():
                if (not cuenta.get(dst)) and first.get(src):
                    cuenta[dst] = first.get(src)
        else:
            raise HTTPException(
                status_code=422,
                detail="Validación AIS falló; usa force_save=true o skip_validation=true para guardar pendiente de validación"
            )

    sid = cuenta.get("schedule_id")
    ivr = cuenta.get("ivr_number")
    dup = check_duplicate_identifiers(sid, ivr)
    if dup:
        raise HTTPException(
            status_code=409,
            detail=f"{dup['field']} duplicado: {dup['value']} ya existe para {dup['existing'].get('email')}"
        )

    if force_save or skip_validation:
        cuenta.setdefault("status", "Pendiente de validación")
        if "is_active" not in cuenta:
            cuenta["is_active"] = False
    else:
        if "is_active" not in cuenta:
            cuenta["is_active"] = True

    cuenta.pop("validation_status", None)
    cuenta.pop("force_save", None)
    cuenta.pop("skip_validation", None)
    cuenta["updated_at"] = datetime.now().isoformat()

    return supabase.table("cuentas_citafast").insert(cuenta).execute().data


@app.put("/cuentas/{id}")
def actualizar_cuenta(id: int, cuenta: dict, x_api_key: str = Header(...)):
    verify(x_api_key)

    cuenta.pop("force_save", None)
    cuenta.pop("skip_validation", None)

    sid = cuenta.get("schedule_id")
    ivr = cuenta.get("ivr_number")
    dup = check_duplicate_identifiers(sid, ivr, exclude_id=id)
    if dup:
        raise HTTPException(
            status_code=409,
            detail=f"{dup['field']} duplicado: {dup['value']} ya existe para {dup['existing'].get('email')}"
        )

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
            # ── TOTAL PERSONAS del comprobante ──
            total_personas = None
            if tbody:
                filas_validas = [r for r in tbody.find_all("tr") if r.find("td") and r.find("td").get_text(strip=True)]
                total_personas = len(filas_validas) if filas_validas else None
            result.append({"schedule_id":sid,"nombre":name,"cita_actual":cita,"asc_date":asc_date,"passport_number":passport,"ds160_number":ds160,"visa_type":visa_type,"ivr_number":ivr_number,"total_personas":total_personas})
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
        # ── IVR NUMBER ──
        ivr_num = None
        ivr_m = _rx.search(r'IVR Account Number[:\s]*<[^>]*>(\d+)', r3.text)
        if ivr_m:
            ivr_num = ivr_m.group(1)
        else:
            for div in soup.find_all("div", class_="columns"):
                txt = div.get_text(strip=True)
                if 'IVR Account Number' in txt:
                    im = _rx.search(r'(\d{7,9})', txt)
                    if im: ivr_num = im.group(1); break
        if ivr_num: updates["ivr_number"] = ivr_num
        # ── TOTAL PERSONAS ──
        if tbody:
            filas_validas = [r for r in tbody.find_all("tr") if r.find("td") and r.find("td").get_text(strip=True)]
            if filas_validas: updates["total_personas"] = len(filas_validas)
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
    verify(x_api_key)
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


@app.get("/monitor/full")
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
    if isinstance(proxies_raw, list):
        lines = [p.strip() for p in proxies_raw if p.strip()]
    else:
        lines = [p.strip() for p in str(proxies_raw).splitlines() if p.strip()]
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
    # Auto-distribuir proxies a cuentas que no tienen
    if inserted > 0:
        try:
            all_px = supabase.table("proxies").select("proxy,status").eq("status","free").execute().data or []
            if all_px:
                px_str = ",".join([p["proxy"].replace("http://","") for p in all_px])
                # Actualizar cuentas sin proxy asignado
                sin_proxy = supabase.table("cuentas_citafast").select("id").is_("proxies","null").execute().data or []
                if sin_proxy:
                    ids = [r["id"] for r in sin_proxy]
                    for cid in ids:
                        # Asignar proxy rotativo
                        px = all_px[cid % len(all_px)]["proxy"].replace("http://","")
                        supabase.table("cuentas_citafast").update({"proxies": px}).eq("id", cid).execute()
        except Exception as _e:
            pass
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
        "runtime": {
            "dry_run": str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on"),
            "csrf_refresh_seconds": int(os.getenv("CSRF_REFRESH_SECONDS", "240")),
            "session_relogin_seconds": int(os.getenv("SESSION_RELOGIN_SECONDS", "540")),
            "empty_dates_backoff_max_seconds": int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15"))
        },
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
async def trazas_http(limit: int=200, api_key: str=Header(None,alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    import re as rx
    try:
        lines = open('/root/nexus.log',encoding='utf-8',errors='ignore').readlines()[-2000:]
        out = []
        cuenta_actual = ''
        for line in lines:
            l = line.strip()
            if not l: continue
            ts = rx.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', l)
            cm = rx.search(r'\[([^\[\]]+@[^\[\]]+)\]', l)
            if cm: cuenta_actual = cm.group(1)
            # Solo líneas relevantes
            kw = ['Login OK','Error fechas','Rotando','Sin cuentas','Cuentas activas','LOGIN','cita','bloqueada','CSRF','Hilos']
            if not any(x in l for x in kw): continue
            # Parsear paso HTTP si existe
            step_m = rx.search(r'(login_page|login_submit|proxy_ip|dashboard|appointment_page|consulate_days|appointment_times)', l)
            method_m = rx.search(r'\b(GET|POST)\b', l)
            status_m = rx.search(r'\b(200|302|401|403|429|500)\b', l)
            url_m = rx.search(r'https?://[^\s\]"]+', l)
            # Extraer fechas disponibles si las hay
            fechas = rx.findall(r'\d{4}-\d{2}-\d{2}', l)
            # Mensaje limpio
            msg = l
            for rm in [ts.group() if ts else '', f'[{cuenta_actual}]' if cuenta_actual else '', '[CF-\d+]', '[MainThread]']:
                msg = rx.sub(rm.replace('[','\\[').replace(']','\\]'), '', msg).strip() if rm else msg
            msg = rx.sub(r'\[CF-\d+\]', '', msg).strip()
            tipo = ('success' if 'Login OK' in l or 'Cuentas activas' in l
                    else 'error' if 'Error' in l or 'bloqueada' in l or 'CSRF' in l
                    else 'warning' if 'Rotando' in l or 'Sin cuentas' in l
                    else 'info')
            out.append({
                'ts': ts.group(1) if ts else '',
                'hora': ts.group(1)[11:] if ts else '',
                'cuenta': cuenta_actual,
                'cuenta_short': cuenta_actual.split('@')[0] if cuenta_actual else '',
                'paso': step_m.group() if step_m else '',
                'method': method_m.group() if method_m else '',
                'status': int(status_m.group()) if status_m else None,
                'url': url_m.group()[:80] if url_m else '',
                'url_short': url_m.group().replace('https://ais.usvisa-info.com/en-do/niv','AIS')[:50] if url_m else '',
                'msg': rx.sub(r'\s+',' ', msg)[:120],
                'fechas_disponibles': fechas[:3] if fechas else [],
                'tipo': tipo
            })
        return {"ok": True, "trazas": out[-limit:], "total": len(out)}
    except Exception as e:
        return {"ok": False, "error": str(e), "trazas": []}

@app.get("/jobs/historial")
async def jobs_historial(limit: int=100, api_key: str=Header(None,alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    import re as rx
    try:
        lines = open('/root/nexus.log',encoding='utf-8',errors='ignore').readlines()
        jobs, cur = [], None
        stats = {'login_ok':0,'success':0,'json_error':0,'http_error':0,'rotando_proxy':0,'blocked':0}
        for line in lines:
            l = line.strip()
            if not l: continue
            ts = rx.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", l)
            t = ts.group(1) if ts else ''
            cm = rx.search(r"\[([^\[\]]+@[^\[\]]+)\]", l)
            cuenta = cm.group(1) if cm else ''
            if 'LOGIN' in l and cuenta:
                if cur: jobs.append(cur)
                cur = {'cuenta':cuenta,'inicio':t,'fin':'','estado':'running','pasos':[],'resumen':''}
            if not cur: continue
            if cuenta and not cur['cuenta']: cur['cuenta'] = cuenta
            um = rx.search(r"https?://[^\s\]]+", l)
            if um:
                sm = rx.search(r"\b(200|302|401|403|429|500)\b", l)
                cur['pasos'].append({'method':'POST' if 'sign_in' in l else 'GET','status':int(sm.group()) if sm else 0,'url':um.group()[:100]})
            if 'Login OK' in l: cur['estado']='login_ok'; cur['fin']=t
            elif 'JSONDecodeError' in l: cur['estado']='json_error'; cur['resumen']='JSONDecodeError'; cur['fin']=t
            elif 'HTTPError' in l: cur['estado']='http_error'; cur['resumen']='HTTPError'; cur['fin']=t
            elif 'Rotando' in l: cur['estado']='rotando_proxy'; cur['resumen']='Proxy rotando'
            elif 'bloqueada' in l.lower(): cur['estado']='blocked'; cur['resumen']='Bloqueada'
        if cur: jobs.append(cur)
        for j in jobs:
            e=j.get('estado','running')
            if e in stats: stats[e]+=1
        jobs.reverse()
        return {"ok":True,"jobs":jobs[:limit],"total":len(jobs),"stats":stats}
    except Exception as e:
        return {"ok":False,"error":str(e),"jobs":[],"stats":{}}

@app.get("/trazas/estructuradas")
async def trazas_estructuradas(
    email: str = None,
    limit: int = 100,
    api_key: str = Header(None, alias="x-api-key")
):
    if api_key != API_KEY: raise HTTPException(403)
    try:
        q = supabase.table("nexus_trazas").select("*").order("ts", desc=True).limit(limit)
        if email: q = q.eq("email", email)
        r = q.execute()
        return {"ok": True, "trazas": r.data or [], "total": len(r.data or [])}
    except Exception as e:
        # Fallback: parsear log igual que antes
        return {"ok": False, "error": str(e), "trazas": []}

@app.get("/cron/tareas")
async def cron_listar(api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    try:
        r = supabase.table("cron_nexus").select("*").order("priority").execute()
        return {"ok": True, "tareas": r.data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/cron/tareas")
async def cron_crear(body: dict, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    ALLOWED = ['start','stop','restart','set_config','clean_logs','rotate_logs']
    if body.get('action') not in ALLOWED:
        raise HTTPException(400, "Accion no permitida")
    try:
        r = supabase.table("cron_nexus").insert({
            "name": body.get("name","Sin nombre"),
            "active": body.get("active", True),
            "action": body.get("action"),
            "config": body.get("config", {}),
            "days": body.get("days", []),
            "start_time": body.get("start_time"),
            "end_time": body.get("end_time"),
            "priority": body.get("priority", 5),
        }).execute()
        return {"ok": True, "tarea": r.data[0] if r.data else {}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.put("/cron/tareas/{id}")
async def cron_editar(id: int, body: dict, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    try:
        supabase.table("cron_nexus").update(body).eq("id", id).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.delete("/cron/tareas/{id}")
async def cron_eliminar(id: int, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    try:
        supabase.table("cron_nexus").delete().eq("id", id).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.patch("/cron/tareas/{id}/toggle")
async def cron_toggle(id: int, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    try:
        r = supabase.table("cron_nexus").select("active").eq("id", id).execute()
        nuevo = not r.data[0]["active"]
        supabase.table("cron_nexus").update({"active": nuevo}).eq("id", id).execute()
        return {"ok": True, "active": nuevo}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/cron/tareas/{id}/ejecutar")
async def cron_ejecutar(id: int, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    try:
        import subprocess as _sp
        r = _sp.run(["python3","/root/cron_nexus_worker.py"],capture_output=True,text=True,timeout=30)
        return {"ok": True, "output": r.stdout+r.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/cron/logs")
async def cron_logs(limit: int = 50, api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    try:
        r = supabase.table("cron_nexus_logs").select("*").order("executed_at", desc=True).limit(limit).execute()
        return {"ok": True, "logs": r.data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/trazas/timing")
async def trazas_timing(api_key: str = Header(None, alias="x-api-key")):
    if api_key != API_KEY: raise HTTPException(403)
    import re as _re
    from datetime import datetime as _dt
    try:
        lines = open('/root/nexus.log', encoding='utf-8', errors='ignore').readlines()[-2000:]
        stats = {'login_ok':0,'fechas_ok':0,'no_match':0,'http_err':0,'citas':0,'proxy_rot':0}
        tiempos = []
        cur = None
        for l in lines:
            if 'Login OK' in l: stats['login_ok']+=1; cur={'ts':l[:23]}
            elif cur and 'Fechas:' in l:
                stats['fechas_ok']+=1
                try:
                    t1=_dt.strptime(cur['ts'],'%Y-%m-%d %H:%M:%S,%f')
                    t2=_dt.strptime(l[:23],'%Y-%m-%d %H:%M:%S,%f')
                    tiempos.append(int((t2-t1).total_seconds()*1000))
                except: pass
                cur=None
            if 'sin match' in l.lower(): stats['no_match']+=1
            if 'HTTPError' in l: stats['http_err']+=1
            if 'CITA AGENDADA' in l or 'CITA!!!' in l: stats['citas']+=1
            if 'Rotando' in l: stats['proxy_rot']+=1
        timing = {}
        if tiempos:
            timing = {'min_ms':min(tiempos),'max_ms':max(tiempos),'avg_ms':int(sum(tiempos)/len(tiempos)),'muestras':len(tiempos)}
        return {'ok':True,'stats':stats,'timing':timing,'efectividad_pct':round(stats['citas']/(stats['login_ok'] or 1)*100,2)}
    except Exception as e:
        return {'ok':False,'error':str(e)}


@app.get("/runtime/config")
def runtime_config_get(x_api_key: str = Header(...)):
    verify(x_api_key)
    return _runtime_load_persisted()


@app.post("/runtime/config")
def runtime_config_set(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    cur = _runtime_load_persisted()
    cfg = {
        "dry_run": _rt_truthy(body.get("dry_run", cur["dry_run"])),
        "csrf_refresh_seconds": int(body.get("csrf_refresh_seconds", cur["csrf_refresh_seconds"]) or cur["csrf_refresh_seconds"]),
        "session_relogin_seconds": int(body.get("session_relogin_seconds", cur["session_relogin_seconds"]) or cur["session_relogin_seconds"]),
        "empty_dates_backoff_max_seconds": int(body.get("empty_dates_backoff_max_seconds", cur["empty_dates_backoff_max_seconds"]) or cur["empty_dates_backoff_max_seconds"]),
    }
    _runtime_save_persisted(cfg)
    return {"success": True, "runtime": cfg, "message": "Configuración runtime guardada en /root/.env.citafast"}


@app.get("/proxies/ranking")
def proxies_ranking(x_api_key: str = Header(...), limit: int = 100):
    verify(x_api_key)

    rows = supabase.table("proxies").select("*").execute().data or []
    now = datetime.now()

    ranked = []
    for r in rows:
        status = (r.get("status") or "free").lower()
        fail_count = int(r.get("fail_count") or 0)
        cooldown_until = r.get("cooldown_until")
        type_ = r.get("type") or "unknown"
        proxy = r.get("proxy") or ""

        score = 100

        if status == "dead":
            score -= 60
        elif status != "free":
            score -= 25

        score -= min(fail_count * 10, 40)

        cooldown_active = False
        if cooldown_until:
            try:
                cooldown_dt = datetime.fromisoformat(str(cooldown_until).replace("Z", "+00:00").replace("+00:00", ""))
                cooldown_active = cooldown_dt > now
            except:
                cooldown_active = False

        if cooldown_active:
            score -= 20

        if score < 0:
            score = 0

        ranked.append({
            "id": r.get("id"),
            "proxy": proxy,
            "type": type_,
            "status": status,
            "fail_count": fail_count,
            "cooldown_until": cooldown_until,
            "score": score
        })

    ranked.sort(key=lambda x: (-x["score"], x["fail_count"], x["status"], x["type"]))
    return {
        "total": len(ranked),
        "top": ranked[:limit],
        "best": ranked[:10],
        "worst": sorted(ranked, key=lambda x: (x["score"], -x["fail_count"]))[:10]
    }


@app.get("/cuentas/status-summary")
def cuentas_status_summary(x_api_key: str = Header(...)):
    verify(x_api_key)
    rows = supabase.table("cuentas_citafast").select("id,is_active,status,country").execute().data or []

    summary = {
        "total": len(rows),
        "active": 0,
        "inactive": 0,
        "agendadas": 0,
        "statuses": {},
        "countries": {}
    }

    for r in rows:
        if r.get("is_active"):
            summary["active"] += 1
        else:
            summary["inactive"] += 1

        status = (r.get("status") or "Sin status").strip()
        summary["statuses"][status] = summary["statuses"].get(status, 0) + 1

        if status.lower() == "cita agendada":
            summary["agendadas"] += 1

        country = (r.get("country") or "unknown").strip().lower()
        summary["countries"][country] = summary["countries"].get(country, 0) + 1

    return summary


@app.get("/cuentas/paused")
def cuentas_paused(x_api_key: str = Header(...), limit: int = 200):
    verify(x_api_key)
    rows = supabase.table("cuentas_citafast").select(
        "id,email,status,is_active,schedule_id,ivr_number,total_personas,last_appointment_date,updated_at"
    ).eq("is_active", False).order("updated_at", desc=True).limit(limit).execute().data or []

    paused = [r for r in rows if (r.get("status") or "").strip().lower() != "cita agendada"]

    return {
        "total": len(paused),
        "items": paused
    }


@app.get("/proxies/health-summary")
def proxies_health_summary(x_api_key: str = Header(...)):
    verify(x_api_key)

    rows = supabase.table("proxies").select(
        "id,proxy,type,status,fail_count,cooldown_until"
    ).execute().data or []

    now = datetime.now()
    ranked = []
    cooldown_active = 0
    free = 0
    dead = 0

    for r in rows:
        status = (r.get("status") or "free").lower()
        fail_count = int(r.get("fail_count") or 0)
        cooldown_until = r.get("cooldown_until")
        type_ = r.get("type") or "unknown"
        proxy = r.get("proxy") or ""

        score = 100

        if status == "free":
            free += 1
        if status == "dead":
            dead += 1
            score -= 60
        elif status != "free":
            score -= 25

        score -= min(fail_count * 10, 40)

        is_cooldown = False
        if cooldown_until:
            try:
                cd = datetime.fromisoformat(str(cooldown_until).replace("Z", "+00:00").replace("+00:00", ""))
                is_cooldown = cd > now
            except:
                is_cooldown = False

        if is_cooldown:
            cooldown_active += 1
            score -= 20

        if score < 0:
            score = 0

        ranked.append({
            "id": r.get("id"),
            "proxy": proxy,
            "type": type_,
            "status": status,
            "fail_count": fail_count,
            "cooldown_until": cooldown_until,
            "score": score
        })

    best = sorted(ranked, key=lambda x: (-x["score"], x["fail_count"], x["status"]))[:10]
    worst = sorted(ranked, key=lambda x: (x["score"], -x["fail_count"], x["status"]))[:10]

    return {
        "total": len(ranked),
        "free": free,
        "dead": dead,
        "cooldown_active": cooldown_active,
        "best": best,
        "worst": worst
    }


@app.get("/kpi/overview")
def kpi_overview(x_api_key: str = Header(...)):
    normalize_expired_ais_blocks()
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()

    cuentas = supabase.table("cuentas_citafast").select("id,is_active,status,schedule_id").execute().data or []
    proxies = supabase.table("proxies").select("status,fail_count,cooldown_until").execute().data or []

    active = len([c for c in cuentas if c.get("is_active")])
    agendadas = len([c for c in cuentas if (c.get("status") or "").strip().lower() == "cita agendada"])
    paused = len([c for c in cuentas if not c.get("is_active") and (c.get("status") or "").strip().lower() != "cita agendada"])

    free = len([p for p in proxies if (p.get("status") or "").lower() == "free"])
    dead = len([p for p in proxies if (p.get("status") or "").lower() == "dead"])

    return {
        "bot": bot_active,
        "cuentas": {
            "total": len(cuentas),
            "active": active,
            "paused": paused,
            "agendadas": agendadas
        },
        "proxies": {
            "total": len(proxies),
            "free": free,
            "dead": dead
        },
        "runtime": {
            "dry_run": str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on"),
            "csrf_refresh_seconds": int(os.getenv("CSRF_REFRESH_SECONDS", "240")),
            "session_relogin_seconds": int(os.getenv("SESSION_RELOGIN_SECONDS", "540")),
            "empty_dates_backoff_max_seconds": int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15"))
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/cuentas/search-ready")
def cuentas_search_ready(x_api_key: str = Header(...), limit: int = 200):
    normalize_expired_ais_blocks()
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "id,email,is_active,status,schedule_id,ivr_number,total_personas,country,updated_at"
    ).eq("is_active", True).limit(limit).execute().data or []

    blocked_words = (
        "bloqueada ais",
        "challenge/captcha ais",
        "sin schedule id",
        "pago/acceso ais"
    )

    ready = []
    excluded = []

    for r in rows:
        status = (r.get("status") or "").strip().lower()
        sid = (r.get("schedule_id") or "").strip()

        if not sid:
            excluded.append({**r, "reason": "sin_schedule_id"})
            continue

        if status == "cita agendada":
            excluded.append({**r, "reason": "agendada"})
            continue

        if any(w in status for w in blocked_words):
            excluded.append({**r, "reason": "estado_terminal"})
            continue

        ready.append(r)

    return {
        "total_active_checked": len(rows),
        "ready_total": len(ready),
        "excluded_total": len(excluded),
        "ready": ready[:limit],
        "excluded": excluded[:limit]
    }


@app.post("/runtime/config/apply")
def runtime_config_apply(body: dict, x_api_key: str = Header(...)):
    return runtime_config_set(body, x_api_key)


@app.get("/cuentas/health-lite")
def cuentas_health_lite(x_api_key: str = Header(...)):
    normalize_expired_ais_blocks()
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "id,email,is_active,status,schedule_id,country"
    ).execute().data or []

    paused_reasons = {}
    ready = 0
    paused = 0
    agendadas = 0
    no_schedule = 0

    for r in rows:
        status = (r.get("status") or "").strip()
        status_l = status.lower()
        sid = (r.get("schedule_id") or "").strip()

        if status_l == "cita agendada":
            agendadas += 1
            continue

        if not sid:
            no_schedule += 1

        if not r.get("is_active"):
            paused += 1
            paused_reasons[status or "Sin status"] = paused_reasons.get(status or "Sin status", 0) + 1
            continue

        blocked_words = (
            "bloqueada ais",
            "challenge/captcha ais",
            "sin schedule id",
            "pago/acceso ais"
        )
        if any(w in status_l for w in blocked_words):
            paused += 1
            paused_reasons[status or "Sin status"] = paused_reasons.get(status or "Sin status", 0) + 1
            continue

        if sid:
            ready += 1

    return {
        "total": len(rows),
        "ready": ready,
        "paused": paused,
        "agendadas": agendadas,
        "no_schedule": no_schedule,
        "paused_reasons": paused_reasons
    }


@app.get("/cuentas/by-country")
def cuentas_by_country(x_api_key: str = Header(...)):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "country,is_active,status"
    ).execute().data or []

    out = {}
    for r in rows:
        country = (r.get("country") or "unknown").strip().lower()
        status = (r.get("status") or "").strip().lower()

        if country not in out:
            out[country] = {
                "total": 0,
                "active": 0,
                "paused": 0,
                "agendadas": 0
            }

        out[country]["total"] += 1
        if r.get("is_active"):
            out[country]["active"] += 1
        else:
            out[country]["paused"] += 1

        if status == "cita agendada":
            out[country]["agendadas"] += 1

    return out


@app.get("/proxies/type-summary")
def proxies_type_summary(x_api_key: str = Header(...)):
    verify(x_api_key)

    rows = supabase.table("proxies").select(
        "type,status,fail_count"
    ).execute().data or []

    out = {}
    for r in rows:
        t = (r.get("type") or "unknown").strip().lower()
        s = (r.get("status") or "free").strip().lower()
        f = int(r.get("fail_count") or 0)

        if t not in out:
            out[t] = {
                "total": 0,
                "free": 0,
                "dead": 0,
                "other": 0,
                "fail_count_sum": 0,
                "avg_fail_count": 0
            }

        out[t]["total"] += 1
        out[t]["fail_count_sum"] += f

        if s == "free":
            out[t]["free"] += 1
        elif s == "dead":
            out[t]["dead"] += 1
        else:
            out[t]["other"] += 1

    for t, v in out.items():
        if v["total"] > 0:
            v["avg_fail_count"] = round(v["fail_count_sum"] / v["total"], 2)

    return out


@app.get("/logs/tail-json")
def logs_tail_json(x_api_key: str = Header(...), lines: int = 100):
    verify(x_api_key)

    import re

    try:
        with open("/root/log_nexus.txt", "r", encoding="utf-8", errors="ignore") as f:
            raw = f.readlines()[-lines:]
    except:
        raw = []

    items = []
    for line in raw:
        txt_line = line.rstrip("\n")

        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \[([^\]]+)\] (.*)$", txt_line)
        if m:
            ts, thread, msg = m.groups()
        else:
            ts, thread, msg = "", "", txt_line

        msg_l = msg.lower()
        if "❌" in msg or "error" in msg_l:
            kind = "error"
        elif "⚠️" in msg or "warn" in msg_l:
            kind = "warning"
        elif "✅" in msg:
            kind = "success"
        else:
            kind = "info"

        items.append({
            "ts": ts,
            "thread": thread,
            "message": msg,
            "kind": kind
        })

    return {
        "total": len(items),
        "items": items
    }


@app.get("/system/readiness-100")
def system_readiness_100(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()

    cuentas = supabase.table("cuentas_citafast").select(
        "id,is_active,status,schedule_id"
    ).execute().data or []
    proxies = supabase.table("proxies").select(
        "status,fail_count"
    ).execute().data or []

    ready_accounts = 0
    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    free_proxies = len([p for p in proxies if (p.get("status") or "").lower() == "free"])
    dead_proxies = len([p for p in proxies if (p.get("status") or "").lower() == "dead"])

    score = 0
    if bot_active == "active":
        score += 25
    if ready_accounts >= 100:
        score += 35
    else:
        score += int((ready_accounts / 100) * 35) if ready_accounts > 0 else 0

    if free_proxies >= 100:
        score += 25
    else:
        score += int((free_proxies / 100) * 25) if free_proxies > 0 else 0

    if dead_proxies == 0:
        score += 15
    elif dead_proxies < 10:
        score += 10
    elif dead_proxies < 25:
        score += 5

    if score > 100:
        score = 100

    return {
        "score": score,
        "bot": bot_active,
        "ready_accounts": ready_accounts,
        "free_proxies": free_proxies,
        "dead_proxies": dead_proxies,
        "runtime": {
            "dry_run": str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on"),
            "csrf_refresh_seconds": int(os.getenv("CSRF_REFRESH_SECONDS", "240")),
            "session_relogin_seconds": int(os.getenv("SESSION_RELOGIN_SECONDS", "540")),
            "empty_dates_backoff_max_seconds": int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15"))
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/security/audit-lite")
def security_audit_lite(x_api_key: str = Header(...)):
    verify(x_api_key)

    env_path = "/root/.env.citafast"
    panel_path = "/var/www/panel/index.html"
    log_path = "/root/log_nexus.txt"

    runtime_keys = {
        "NEXUS_DRY_RUN": os.getenv("NEXUS_DRY_RUN"),
        "NEXUS_CSRF_REFRESH_SECONDS": os.getenv("NEXUS_CSRF_REFRESH_SECONDS"),
        "NEXUS_SESSION_RELOGIN_SECONDS": os.getenv("NEXUS_SESSION_RELOGIN_SECONDS"),
        "NEXUS_EMPTY_DATES_BACKOFF_MAX_SECONDS": os.getenv("NEXUS_EMPTY_DATES_BACKOFF_MAX_SECONDS"),
    }

    service_names = ["nexus", "botvps", "citasflash-api", "nginx"]
    services = {}
    for svc in service_names:
        try:
            st = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True).stdout.strip()
        except:
            st = "error"
        services[svc] = st

    return {
        "api_key_configured": bool(API_KEY),
        "resend_key_configured": bool(RESEND_KEY),
        "env_exists": os.path.exists(env_path),
        "panel_exists": os.path.exists(panel_path),
        "log_exists": os.path.exists(log_path),
        "runtime_keys": {k: bool(v is not None) for k, v in runtime_keys.items()},
        "services": services,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/system/services")
def system_services(x_api_key: str = Header(...)):
    verify(x_api_key)

    service_names = ["nexus", "botvps", "citasflash-api", "nginx"]
    out = {}

    for svc in service_names:
        try:
            st = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True).stdout.strip()
        except:
            st = "error"
        out[svc] = st

    return {
        "services": out,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/system/resources")
def system_resources(x_api_key: str = Header(...)):
    verify(x_api_key)
    import psutil

    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    try:
        load1, load5, load15 = os.getloadavg()
        load = {"load1": round(load1, 2), "load5": round(load5, 2), "load15": round(load15, 2)}
    except:
        load = {"load1": None, "load5": None, "load15": None}

    try:
        nexus_proc = int(subprocess.run(["bash", "-lc", "pgrep -fc 'nexus.py'"], capture_output=True, text=True).stdout.strip() or "0")
    except:
        nexus_proc = 0

    try:
        py_proc = int(subprocess.run(["bash", "-lc", "pgrep -fc 'python'"], capture_output=True, text=True).stdout.strip() or "0")
    except:
        py_proc = 0

    return {
        "cpu_percent": cpu,
        "ram": {
            "used_percent": ram.percent,
            "total_gb": round(ram.total / 1024 / 1024 / 1024, 1),
            "available_gb": round(ram.available / 1024 / 1024 / 1024, 1)
        },
        "disk": {
            "used_percent": disk.percent,
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 1)
        },
        "load": load,
        "processes": {
            "nexus_py": nexus_proc,
            "python_total": py_proc
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/trazas/summary")
def trazas_summary(x_api_key: str = Header(...), limit: int = 1000):
    verify(x_api_key)

    rows = supabase.table("nexus_trazas").select("tipo,email").limit(limit).execute().data or []

    by_type = {}
    emails = set()

    for r in rows:
        tipo = (r.get("tipo") or "unknown").strip().lower()
        email = (r.get("email") or "").strip().lower()
        by_type[tipo] = by_type.get(tipo, 0) + 1
        if email:
            emails.add(email)

    return {
        "total": len(rows),
        "by_type": by_type,
        "unique_accounts": len(emails)
    }


@app.get("/jobs/recent-errors")
def jobs_recent_errors(x_api_key: str = Header(...), lines: int = 300):
    verify(x_api_key)

    try:
        with open("/root/log_nexus.txt", "r", encoding="utf-8", errors="ignore") as f:
            raw = f.readlines()[-lines:]
    except:
        raw = []

    stats = {
        "errors": 0,
        "warnings": 0,
        "success": 0,
        "login_ok": 0,
        "citas": 0,
        "pauses": 0,
        "sin_fechas": 0
    }

    for line in raw:
        l = line.lower()

        if "❌" in line or " error" in l or "error:" in l:
            stats["errors"] += 1
        if "⚠️" in line or "warn" in l:
            stats["warnings"] += 1
        if "✅" in line:
            stats["success"] += 1
        if "login ok" in l:
            stats["login_ok"] += 1
        if "cita agendada" in l or "cita capturada exitosamente" in l:
            stats["citas"] += 1
        if "pause " in l or "paus" in l:
            stats["pauses"] += 1
        if "sin fechas" in l:
            stats["sin_fechas"] += 1

    return {
        "lines_checked": len(raw),
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/runtime/config/validate")
def runtime_config_validate(x_api_key: str = Header(...)):
    verify(x_api_key)

    dry_run = str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on")
    csrf = int(os.getenv("CSRF_REFRESH_SECONDS", "240"))
    session = int(os.getenv("SESSION_RELOGIN_SECONDS", "540"))
    empty_backoff = int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15"))

    warnings = []

    if csrf < 120:
        warnings.append("csrf_refresh_seconds demasiado bajo")
    if csrf > 420:
        warnings.append("csrf_refresh_seconds demasiado alto")
    if session < 420:
        warnings.append("session_relogin_seconds demasiado bajo")
    if session > 620:
        warnings.append("session_relogin_seconds demasiado alto")
    if empty_backoff < 1:
        warnings.append("empty_dates_backoff_max_seconds inválido")
    if empty_backoff > 60:
        warnings.append("empty_dates_backoff_max_seconds alto")

    return {
        "dry_run": dry_run,
        "csrf_refresh_seconds": csrf,
        "session_relogin_seconds": session,
        "empty_dates_backoff_max_seconds": empty_backoff,
        "warnings": warnings,
        "ok": len(warnings) == 0,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/system/process-map")
def system_process_map(x_api_key: str = Header(...)):
    verify(x_api_key)

    def sh(cmd):
        try:
            return subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True).stdout.strip()
        except:
            return ""

    nexus_ps = sh("pgrep -af 'nexus.py'")
    api_ps = sh("pgrep -af 'api_control'")
    uvicorn_ps = sh("pgrep -af 'uvicorn'")
    python_ps = sh("pgrep -af 'python' | head -n 20")

    return {
        "counts": {
            "nexus": int(sh("pgrep -fc 'nexus.py'") or "0"),
            "api_control": int(sh("pgrep -fc 'api_control'") or "0"),
            "uvicorn": int(sh("pgrep -fc 'uvicorn'") or "0"),
            "python": int(sh("pgrep -fc 'python'") or "0")
        },
        "samples": {
            "nexus": nexus_ps.splitlines(),
            "api_control": api_ps.splitlines(),
            "uvicorn": uvicorn_ps.splitlines(),
            "python": python_ps.splitlines()
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/cuentas/terminal-statuses")
def cuentas_terminal_statuses(x_api_key: str = Header(...), limit: int = 300):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "id,email,status,is_active,schedule_id,ivr_number,total_personas,updated_at"
    ).limit(limit).execute().data or []

    terminal_words = (
        "bloqueada ais",
        "challenge/captcha ais",
        "sin schedule id",
        "pago/acceso ais"
    )

    items = []
    summary = {}

    for r in rows:
        status = (r.get("status") or "").strip()
        status_l = status.lower()
        if any(w in status_l for w in terminal_words):
            items.append(r)
            summary[status] = summary.get(status, 0) + 1

    return {
        "total": len(items),
        "summary": summary,
        "items": items[:limit]
    }


@app.get("/proxies/cooldown-active")
def proxies_cooldown_active(x_api_key: str = Header(...), limit: int = 200):
    verify(x_api_key)

    rows = supabase.table("proxies").select(
        "id,proxy,type,status,fail_count,cooldown_until"
    ).limit(limit).execute().data or []

    now = datetime.now()
    items = []

    for r in rows:
        cooldown_until = r.get("cooldown_until")
        if not cooldown_until:
            continue
        try:
            cd = datetime.fromisoformat(str(cooldown_until).replace("Z", "+00:00").replace("+00:00", ""))
            if cd > now:
                items.append(r)
        except:
            continue

    items.sort(key=lambda x: str(x.get("cooldown_until") or ""))
    return {
        "total": len(items),
        "items": items[:limit]
    }


@app.get("/dashboard/home")
def dashboard_home(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()

    cuentas = supabase.table("cuentas_citafast").select(
        "id,is_active,status,schedule_id,country"
    ).execute().data or []
    proxies = supabase.table("proxies").select(
        "status,fail_count,cooldown_until,type"
    ).execute().data or []

    total_cuentas = len(cuentas)
    active_cuentas = len([c for c in cuentas if c.get("is_active")])
    agendadas = len([c for c in cuentas if (c.get("status") or "").strip().lower() == "cita agendada"])
    paused = len([c for c in cuentas if not c.get("is_active") and (c.get("status") or "").strip().lower() != "cita agendada"])

    free_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "free"])
    dead_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "dead"])

    ready_accounts = 0
    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    readiness = 0
    if bot_active == "active":
        readiness += 25
    readiness += min(int((ready_accounts / 100) * 35), 35) if ready_accounts > 0 else 0
    readiness += min(int((free_proxies / 100) * 25), 25) if free_proxies > 0 else 0
    if dead_proxies == 0:
        readiness += 15
    elif dead_proxies < 10:
        readiness += 10
    elif dead_proxies < 25:
        readiness += 5
    if readiness > 100:
        readiness = 100

    return {
        "bot": bot_active,
        "cuentas": {
            "total": total_cuentas,
            "active": active_cuentas,
            "paused": paused,
            "agendadas": agendadas,
            "ready_accounts": ready_accounts
        },
        "proxies": {
            "total": len(proxies),
            "free": free_proxies,
            "dead": dead_proxies
        },
        "runtime": {
            "dry_run": str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on"),
            "csrf_refresh_seconds": int(os.getenv("CSRF_REFRESH_SECONDS", "240")),
            "session_relogin_seconds": int(os.getenv("SESSION_RELOGIN_SECONDS", "540")),
            "empty_dates_backoff_max_seconds": int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15"))
        },
        "readiness_100": readiness,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/dashboard/ops-board")
def dashboard_ops_board(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()
    cuentas = supabase.table("cuentas_citafast").select("id,is_active,status,schedule_id").execute().data or []
    proxies = supabase.table("proxies").select("status,fail_count,cooldown_until").execute().data or []

    total_cuentas = len(cuentas)
    active_cuentas = len([c for c in cuentas if c.get("is_active")])
    agendadas = len([c for c in cuentas if (c.get("status") or "").strip().lower() == "cita agendada"])
    paused = len([c for c in cuentas if not c.get("is_active") and (c.get("status") or "").strip().lower() != "cita agendada"])

    ready_accounts = 0
    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    free_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "free"])
    dead_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "dead"])

    readiness = 0
    if bot_active == "active":
        readiness += 25
    readiness += min(int((ready_accounts / 100) * 35), 35) if ready_accounts > 0 else 0
    readiness += min(int((free_proxies / 100) * 25), 25) if free_proxies > 0 else 0
    if dead_proxies == 0:
        readiness += 15
    elif dead_proxies < 10:
        readiness += 10
    elif dead_proxies < 25:
        readiness += 5
    if readiness > 100:
        readiness = 100

    return {
        "bot": bot_active,
        "cuentas": {
            "total": total_cuentas,
            "active": active_cuentas,
            "paused": paused,
            "agendadas": agendadas,
            "ready_accounts": ready_accounts
        },
        "proxies": {
            "total": len(proxies),
            "free": free_proxies,
            "dead": dead_proxies
        },
        "runtime": {
            "dry_run": str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on"),
            "csrf_refresh_seconds": int(os.getenv("CSRF_REFRESH_SECONDS", "240")),
            "session_relogin_seconds": int(os.getenv("SESSION_RELOGIN_SECONDS", "540")),
            "empty_dates_backoff_max_seconds": int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15"))
        },
        "readiness_100": readiness,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/cuentas/recent-updates")
def cuentas_recent_updates(x_api_key: str = Header(...), limit: int = 50):
    verify(x_api_key)
    rows = supabase.table("cuentas_citafast").select(
        "id,email,status,is_active,schedule_id,ivr_number,total_personas,updated_at"
    ).order("updated_at", desc=True).limit(limit).execute().data or []
    return {
        "total": len(rows),
        "items": rows
    }


@app.get("/proxies/ready-pool")
def proxies_ready_pool(x_api_key: str = Header(...), limit: int = 100):
    verify(x_api_key)

    rows = supabase.table("proxies").select(
        "id,proxy,type,status,fail_count,cooldown_until"
    ).execute().data or []

    now = datetime.now()
    items = []

    for r in rows:
        status = (r.get("status") or "").strip().lower()
        if status != "free":
            continue

        cooldown_until = r.get("cooldown_until")
        cooldown_active = False
        if cooldown_until:
            try:
                cd = datetime.fromisoformat(str(cooldown_until).replace("Z", "+00:00").replace("+00:00", ""))
                cooldown_active = cd > now
            except:
                cooldown_active = False

        if cooldown_active:
            continue

        items.append({
            "id": r.get("id"),
            "proxy": r.get("proxy"),
            "type": r.get("type"),
            "status": status,
            "fail_count": int(r.get("fail_count") or 0),
            "cooldown_until": cooldown_until
        })

    items.sort(key=lambda x: (x["fail_count"], x["type"] or "", x["proxy"] or ""))
    return {
        "total": len(items),
        "items": items[:limit]
    }


@app.get("/runtime/profiles")
def runtime_profiles(x_api_key: str = Header(...)):
    verify(x_api_key)
    return {
        "conservador": {
            "dry_run": False,
            "csrf_refresh_seconds": 300,
            "session_relogin_seconds": 540,
            "empty_dates_backoff_max_seconds": 20
        },
        "normal": {
            "dry_run": False,
            "csrf_refresh_seconds": 240,
            "session_relogin_seconds": 540,
            "empty_dates_backoff_max_seconds": 15
        },
        "miercoles": {
            "dry_run": False,
            "csrf_refresh_seconds": 240,
            "session_relogin_seconds": 540,
            "empty_dates_backoff_max_seconds": 8
        },
        "prueba": {
            "dry_run": True,
            "csrf_refresh_seconds": 240,
            "session_relogin_seconds": 540,
            "empty_dates_backoff_max_seconds": 10
        }
    }


@app.get("/dashboard/alerts")
def dashboard_alerts(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()
    cuentas = supabase.table("cuentas_citafast").select("id,is_active,status,schedule_id").execute().data or []
    proxies = supabase.table("proxies").select("status,cooldown_until").execute().data or []

    alerts = []

    if bot_active != "active":
        alerts.append({"level": "critical", "code": "BOT_DOWN", "message": "nexus no está activo"})

    ready_accounts = 0
    paused_accounts = 0
    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if not c.get("is_active") and status != "cita agendada":
            paused_accounts += 1
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    free_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "free"])
    dead_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "dead"])

    if ready_accounts < 25:
        alerts.append({"level": "warning", "code": "LOW_READY_ACCOUNTS", "message": f"solo {ready_accounts} cuentas listas"})
    if free_proxies < 20:
        alerts.append({"level": "warning", "code": "LOW_FREE_PROXIES", "message": f"solo {free_proxies} proxies libres"})
    if dead_proxies >= 20:
        alerts.append({"level": "warning", "code": "HIGH_DEAD_PROXIES", "message": f"{dead_proxies} proxies muertos"})
    if paused_accounts >= 20:
        alerts.append({"level": "info", "code": "MANY_PAUSED_ACCOUNTS", "message": f"{paused_accounts} cuentas pausadas"})
    if str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on"):
        alerts.append({"level": "info", "code": "DRY_RUN_ON", "message": "el sistema está en modo prueba"})

    return {
        "total": len(alerts),
        "items": alerts,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/runtime/config/export")
def runtime_config_export(x_api_key: str = Header(...)):
    verify(x_api_key)
    keys = [
        "NEXUS_DRY_RUN",
        "NEXUS_CSRF_REFRESH_SECONDS",
        "NEXUS_SESSION_RELOGIN_SECONDS",
        "NEXUS_EMPTY_DATES_BACKOFF_MAX_SECONDS",
        "NEXUS_TRANSIENT_BACKOFF_MAX_SECONDS",
        "NEXUS_HEARTBEAT_SECONDS",
    ]
    return {
        "env": {k: os.getenv(k) for k in keys},
        "timestamp": datetime.now().isoformat()
    }


@app.post("/runtime/config/backup")
def runtime_config_backup(x_api_key: str = Header(...)):
    verify(x_api_key)

    env_path = "/root/.env.citafast"
    backup_dir = "/root/env_backups"
    os.makedirs(backup_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f".env.citafast_{ts}.bak")

    if not os.path.exists(env_path):
        raise HTTPException(status_code=404, detail="ENV no encontrado")

    with open(env_path, "r", encoding="utf-8") as src:
        data = src.read()
    with open(dest, "w", encoding="utf-8") as dst:
        dst.write(data)

    return {
        "success": True,
        "backup_file": dest,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/runtime/config/backups")
def runtime_config_backups(x_api_key: str = Header(...), limit: int = 20):
    verify(x_api_key)

    backup_dir = Path("/root/env_backups")
    if not backup_dir.exists():
        return {"total": 0, "items": []}

    files = sorted(
        [f for f in backup_dir.glob(".env.citafast_*.bak") if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    items = []
    for f in files[:limit]:
        st = f.stat()
        items.append({
            "file": str(f),
            "size_bytes": st.st_size,
            "mtime": datetime.fromtimestamp(st.st_mtime).isoformat()
        })

    return {
        "total": len(files),
        "items": items
    }


@app.get("/dashboard/traffic-light")
def dashboard_traffic_light(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()
    cuentas = supabase.table("cuentas_citafast").select("id,is_active,status,schedule_id").execute().data or []
    proxies = supabase.table("proxies").select("status").execute().data or []

    ready_accounts = 0
    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    free_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "free"])

    if bot_active != "active":
        color = "red"
    elif ready_accounts < 25 or free_proxies < 20:
        color = "yellow"
    else:
        color = "green"

    return {
        "color": color,
        "bot": bot_active,
        "ready_accounts": ready_accounts,
        "free_proxies": free_proxies,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/logs/search")
def logs_search(x_api_key: str = Header(...), q: str = "", lines: int = 500):
    verify(x_api_key)

    try:
        with open("/root/log_nexus.txt", "r", encoding="utf-8", errors="ignore") as f:
            raw = f.readlines()[-lines:]
    except:
        raw = []

    ql = (q or "").strip().lower()
    items = []

    for line in raw:
        txt_line = line.rstrip("\n")
        if ql and ql not in txt_line.lower():
            continue
        items.append(txt_line)

    return {
        "query": q,
        "lines_checked": len(raw),
        "matches": len(items),
        "items": items
    }


@app.get("/runtime/config/recommendations")
def runtime_config_recommendations(x_api_key: str = Header(...)):
    verify(x_api_key)

    dry_run = str(os.getenv("DRY_RUN", "true")).lower() in ("1", "true", "yes", "on")
    csrf = int(os.getenv("CSRF_REFRESH_SECONDS", "240"))
    session = int(os.getenv("SESSION_RELOGIN_SECONDS", "540"))
    empty_backoff = int(os.getenv("EMPTY_DATES_BACKOFF_MAX_SECONDS", "15"))
    transient_backoff = int(os.getenv("NEXUS_TRANSIENT_BACKOFF_MAX_SECONDS", "20"))
    heartbeat = int(os.getenv("NEXUS_HEARTBEAT_SECONDS", "300"))

    rec = []

    if dry_run:
        rec.append({"level": "info", "message": "Modo prueba activo; útil para validar sin booking real."})
    else:
        rec.append({"level": "info", "message": "Modo real activo."})

    if csrf < 180:
        rec.append({"level": "warning", "message": "CSRF muy agresivo; podría generar tráfico innecesario."})
    elif csrf > 360:
        rec.append({"level": "warning", "message": "CSRF muy alto; puede aumentar riesgo de token vencido."})
    else:
        rec.append({"level": "success", "message": "CSRF en rango sano."})

    if session < 480:
        rec.append({"level": "warning", "message": "Re-login muy frecuente."})
    elif session > 600:
        rec.append({"level": "warning", "message": "Re-login demasiado tardío para una sesión corta."})
    else:
        rec.append({"level": "success", "message": "Re-login en rango sano."})

    if empty_backoff > 20:
        rec.append({"level": "warning", "message": "Backoff por fechas vacías alto; puede bajar sensibilidad."})
    if transient_backoff > 30:
        rec.append({"level": "warning", "message": "Backoff transitorio alto; revisar proxies/latencia."})
    if heartbeat > 600:
        rec.append({"level": "warning", "message": "Heartbeat demasiado espaciado; cuentas pueden verse silenciosas."})

    return {
        "runtime": {
            "dry_run": dry_run,
            "csrf_refresh_seconds": csrf,
            "session_relogin_seconds": session,
            "empty_dates_backoff_max_seconds": empty_backoff,
            "transient_backoff_max_seconds": transient_backoff,
            "heartbeat_seconds": heartbeat
        },
        "recommendations": rec,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/cuentas/ready-by-country")
def cuentas_ready_by_country(x_api_key: str = Header(...)):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "country,is_active,status,schedule_id"
    ).execute().data or []

    out = {}
    blocked_words = ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")

    for r in rows:
        country = (r.get("country") or "unknown").strip().lower()
        if country not in out:
            out[country] = {"ready": 0, "total": 0}

        out[country]["total"] += 1

        status = (r.get("status") or "").strip().lower()
        sid = (r.get("schedule_id") or "").strip()
        if r.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in blocked_words):
                out[country]["ready"] += 1

    return out


@app.get("/proxies/failcount-summary")
def proxies_failcount_summary(x_api_key: str = Header(...)):
    verify(x_api_key)

    rows = supabase.table("proxies").select("id,proxy,type,status,fail_count").execute().data or []

    total = len(rows)
    fail_sum = 0
    top_fail = []

    for r in rows:
        fail = int(r.get("fail_count") or 0)
        fail_sum += fail
        top_fail.append({
            "id": r.get("id"),
            "proxy": r.get("proxy"),
            "type": r.get("type"),
            "status": r.get("status"),
            "fail_count": fail
        })

    top_fail.sort(key=lambda x: (-x["fail_count"], x["status"] or "", x["type"] or ""))
    avg_fail = round((fail_sum / total), 2) if total > 0 else 0

    return {
        "total": total,
        "avg_fail_count": avg_fail,
        "top_fail": top_fail[:20]
    }


@app.get("/dashboard/presidency-summary")
def dashboard_presidency_summary(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()
    cuentas = supabase.table("cuentas_citafast").select("id,is_active,status,schedule_id").execute().data or []
    proxies = supabase.table("proxies").select("status").execute().data or []

    total_cuentas = len(cuentas)
    active_cuentas = len([c for c in cuentas if c.get("is_active")])
    agendadas = len([c for c in cuentas if (c.get("status") or "").strip().lower() == "cita agendada"])
    paused = len([c for c in cuentas if not c.get("is_active") and (c.get("status") or "").strip().lower() != "cita agendada"])
    ready_accounts = 0

    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    free_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "free"])
    dead_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "dead"])

    return {
        "headline": {
            "bot": bot_active,
            "cuentas_ready": ready_accounts,
            "proxies_free": free_proxies
        },
        "summary": {
            "cuentas_total": total_cuentas,
            "cuentas_activas": active_cuentas,
            "cuentas_pausadas": paused,
            "citas_agendadas": agendadas,
            "proxies_muertos": dead_proxies
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/logs/kinds-summary")
def logs_kinds_summary(x_api_key: str = Header(...), lines: int = 500):
    verify(x_api_key)

    try:
        with open("/root/log_nexus.txt", "r", encoding="utf-8", errors="ignore") as f:
            raw = f.readlines()[-lines:]
    except:
        raw = []

    out = {
        "info": 0,
        "warning": 0,
        "error": 0,
        "success": 0
    }

    for line in raw:
        l = line.lower()
        if "❌" in line or " error" in l or "error:" in l:
            out["error"] += 1
        elif "⚠️" in line or "warn" in l:
            out["warning"] += 1
        elif "✅" in line:
            out["success"] += 1
        else:
            out["info"] += 1

    return {
        "lines_checked": len(raw),
        "summary": out,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/runtime/config/restore-last")
def runtime_config_restore_last(x_api_key: str = Header(...)):
    verify(x_api_key)

    backup_dir = Path("/root/env_backups")
    files = sorted(
        [f for f in backup_dir.glob(".env.citafast_*.bak") if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    if not files:
        raise HTTPException(status_code=404, detail="No hay backups")

    src = files[0]
    env_path = "/root/.env.citafast"

    data = src.read_text(encoding="utf-8")
    Path(env_path).write_text(data, encoding="utf-8")

    for line in data.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k] = v

    return {
        "success": True,
        "restored_from": str(src),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/runtime/config/restore")
async def runtime_config_restore(request: Request, x_api_key: str = Header(...)):
    verify(x_api_key)

    body = await request.json()
    file_path = str(body.get("file") or "").strip()
    if not file_path:
        raise HTTPException(status_code=400, detail="file requerido")

    src = Path(file_path)
    backup_dir = Path("/root/env_backups").resolve()

    try:
        resolved = src.resolve()
    except:
        raise HTTPException(status_code=400, detail="archivo inválido")

    if backup_dir not in resolved.parents:
        raise HTTPException(status_code=403, detail="archivo fuera de env_backups")
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="backup no encontrado")

    env_path = "/root/.env.citafast"
    data = resolved.read_text(encoding="utf-8")
    Path(env_path).write_text(data, encoding="utf-8")

    for line in data.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k] = v

    return {
        "success": True,
        "restored_from": str(resolved),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/cuentas/health-score")
def cuentas_health_score(x_api_key: str = Header(...), limit: int = 300):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "id,email,is_active,status,schedule_id,ivr_number,total_personas,last_appointment_date,updated_at,country"
    ).limit(limit).execute().data or []

    items = []
    terminal_words = ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")

    for r in rows:
        score = 100
        status = (r.get("status") or "").strip()
        status_l = status.lower()
        sid = (r.get("schedule_id") or "").strip()

        if not r.get("is_active"):
            score -= 35
        if not sid:
            score -= 25
        if status_l == "cita agendada":
            score -= 10
        if any(w in status_l for w in terminal_words):
            score -= 40
        if not r.get("ivr_number"):
            score -= 5
        if not r.get("total_personas"):
            score -= 5

        if score < 0:
            score = 0

        items.append({
            "id": r.get("id"),
            "email": r.get("email"),
            "country": r.get("country"),
            "status": status,
            "schedule_id": r.get("schedule_id"),
            "ivr_number": r.get("ivr_number"),
            "total_personas": r.get("total_personas"),
            "is_active": r.get("is_active"),
            "updated_at": r.get("updated_at"),
            "score": score
        })

    items.sort(key=lambda x: (-x["score"], x["status"] or "", x["email"] or ""))
    return {
        "total": len(items),
        "items": items
    }


@app.get("/cuentas/health-score-summary")
def cuentas_health_score_summary(x_api_key: str = Header(...), limit: int = 300):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "id,email,is_active,status,schedule_id,ivr_number,total_personas,updated_at"
    ).limit(limit).execute().data or []

    items = []
    terminal_words = ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")

    for r in rows:
        score = 100
        status = (r.get("status") or "").strip()
        status_l = status.lower()
        sid = (r.get("schedule_id") or "").strip()

        if not r.get("is_active"):
            score -= 35
        if not sid:
            score -= 25
        if status_l == "cita agendada":
            score -= 10
        if any(w in status_l for w in terminal_words):
            score -= 40
        if not r.get("ivr_number"):
            score -= 5
        if not r.get("total_personas"):
            score -= 5
        if score < 0:
            score = 0

        items.append({
            "id": r.get("id"),
            "email": r.get("email"),
            "status": status,
            "score": score,
            "updated_at": r.get("updated_at")
        })

    best = sorted(items, key=lambda x: (-x["score"], x["email"] or ""))[:20]
    worst = sorted(items, key=lambda x: (x["score"], x["email"] or ""))[:20]
    avg = round(sum(i["score"] for i in items) / len(items), 2) if items else 0

    return {
        "total": len(items),
        "avg_score": avg,
        "best": best,
        "worst": worst
    }


@app.get("/security/route-audit")
def security_route_audit(x_api_key: str = Header(...)):
    verify(x_api_key)

    route_map = {}
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = tuple(sorted(getattr(route, "methods", []) or []))
        if not path:
            continue
        key = (path, methods)
        route_map[key] = route_map.get(key, 0) + 1

    duplicates = []
    for (path, methods), count in route_map.items():
        if count > 1:
            duplicates.append({
                "path": path,
                "methods": list(methods),
                "count": count
            })

    risky = []
    for route in app.routes:
        path = getattr(route, "path", "") or ""
        methods = list(sorted(getattr(route, "methods", []) or []))
        if path.startswith("/auth/") or path.startswith("/cmd/") or path.startswith("/runtime/"):
            risky.append({"path": path, "methods": methods})

    return {
        "duplicates_total": len(duplicates),
        "duplicates": duplicates,
        "sensitive_routes_total": len(risky),
        "sensitive_routes": risky,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/dashboard/menu")
def dashboard_menu(x_api_key: str = Header(...)):
    verify(x_api_key)
    return {
        "items": [
            {"key": "dashboard", "label": "Dashboard", "icon": "layout-dashboard"},
            {"key": "cuentas", "label": "Cuentas", "icon": "users"},
            {"key": "proxies", "label": "Proxies", "icon": "globe"},
            {"key": "operacion", "label": "Operación", "icon": "play-circle"},
            {"key": "monitor", "label": "KPI / Monitor", "icon": "activity"},
            {"key": "trazas", "label": "Trazas", "icon": "scroll-text"},
            {"key": "auth", "label": "Auth", "icon": "shield"}
        ],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/dashboard/cards")
def dashboard_cards(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()
    cuentas = supabase.table("cuentas_citafast").select("id,is_active,status,schedule_id").execute().data or []
    proxies = supabase.table("proxies").select("status").execute().data or []

    total_cuentas = len(cuentas)
    active_cuentas = len([c for c in cuentas if c.get("is_active")])
    agendadas = len([c for c in cuentas if (c.get("status") or "").strip().lower() == "cita agendada"])
    free_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "free"])
    dead_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "dead"])

    ready_accounts = 0
    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    return {
        "cards": [
            {"key": "bot", "label": "Bot Nexus", "value": bot_active},
            {"key": "ready_accounts", "label": "Cuentas listas", "value": ready_accounts},
            {"key": "active_accounts", "label": "Cuentas activas", "value": active_cuentas},
            {"key": "scheduled", "label": "Citas agendadas", "value": agendadas},
            {"key": "free_proxies", "label": "Proxies libres", "value": free_proxies},
            {"key": "dead_proxies", "label": "Proxies muertos", "value": dead_proxies},
            {"key": "total_accounts", "label": "Cuentas totales", "value": total_cuentas},
        ],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/dashboard/table-ready-accounts")
def dashboard_table_ready_accounts(x_api_key: str = Header(...), limit: int = 100):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select(
        "id,email,is_active,status,schedule_id,ivr_number,total_personas,country,updated_at,last_appointment_date"
    ).eq("is_active", True).limit(limit).execute().data or []

    blocked_words = ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")
    ready = []

    for r in rows:
        status = (r.get("status") or "").strip().lower()
        sid = (r.get("schedule_id") or "").strip()
        if sid and status != "cita agendada" and not any(x in status for x in blocked_words):
            ready.append(r)

    ready.sort(key=lambda x: ((x.get("country") or ""), (x.get("email") or "")))
    return {
        "total": len(ready),
        "items": ready[:limit]
    }


@app.get("/dashboard/table-proxies")
def dashboard_table_proxies(x_api_key: str = Header(...), limit: int = 20):
    verify(x_api_key)

    rows = supabase.table("proxies").select(
        "id,proxy,type,status,fail_count,cooldown_until"
    ).execute().data or []

    ranked = []
    now = datetime.now()

    for r in rows:
        status = (r.get("status") or "free").lower()
        fail_count = int(r.get("fail_count") or 0)
        cooldown_until = r.get("cooldown_until")

        score = 100
        if status == "dead":
            score -= 60
        elif status != "free":
            score -= 25
        score -= min(fail_count * 10, 40)

        if cooldown_until:
            try:
                cd = datetime.fromisoformat(str(cooldown_until).replace("Z", "+00:00").replace("+00:00", ""))
                if cd > now:
                    score -= 20
            except:
                pass

        if score < 0:
            score = 0

        ranked.append({
            "id": r.get("id"),
            "proxy": r.get("proxy"),
            "type": r.get("type"),
            "status": status,
            "fail_count": fail_count,
            "cooldown_until": cooldown_until,
            "score": score
        })

    best = sorted(ranked, key=lambda x: (-x["score"], x["fail_count"], x["proxy"] or ""))[:limit]
    worst = sorted(ranked, key=lambda x: (x["score"], -x["fail_count"], x["proxy"] or ""))[:limit]

    return {
        "best": best,
        "worst": worst,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/dashboard/executive-brief")
def dashboard_executive_brief(x_api_key: str = Header(...)):
    verify(x_api_key)

    bot_active = subprocess.run(["systemctl","is-active","nexus"], capture_output=True, text=True).stdout.strip()
    cuentas = supabase.table("cuentas_citafast").select("id,is_active,status,schedule_id").execute().data or []
    proxies = supabase.table("proxies").select("status").execute().data or []

    total_cuentas = len(cuentas)
    active_cuentas = len([c for c in cuentas if c.get("is_active")])
    agendadas = len([c for c in cuentas if (c.get("status") or "").strip().lower() == "cita agendada"])
    paused = len([c for c in cuentas if not c.get("is_active") and (c.get("status") or "").strip().lower() != "cita agendada"])
    free_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "free"])
    dead_proxies = len([p for p in proxies if (p.get("status") or "").strip().lower() == "dead"])

    ready_accounts = 0
    for c in cuentas:
        status = (c.get("status") or "").strip().lower()
        sid = (c.get("schedule_id") or "").strip()
        if c.get("is_active") and sid and status != "cita agendada":
            if not any(x in status for x in ("bloqueada ais", "challenge/captcha ais", "sin schedule id", "pago/acceso ais")):
                ready_accounts += 1

    return {
        "headline": f"Bot={bot_active} | Ready={ready_accounts} | FreeProxies={free_proxies}",
        "summary": {
            "cuentas_total": total_cuentas,
            "cuentas_activas": active_cuentas,
            "cuentas_pausadas": paused,
            "citas_agendadas": agendadas,
            "proxies_libres": free_proxies,
            "proxies_muertos": dead_proxies
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/checkpoints/list")
def checkpoints_list(x_api_key: str = Header(...), limit: int = 50):
    verify(x_api_key)

    root = Path("/root")
    files = sorted(
        [f for f in root.glob("checkpoint_nexus*.tar.gz") if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    items = []
    for f in files[:limit]:
        st = f.stat()
        items.append({
            "file": str(f),
            "size_bytes": st.st_size,
            "mtime": datetime.fromtimestamp(st.st_mtime).isoformat()
        })

    return {
        "total": len(files),
        "items": items
    }


@app.get("/checkpoints/latest")
def checkpoints_latest(x_api_key: str = Header(...)):
    verify(x_api_key)

    root = Path("/root")
    files = sorted(
        [f for f in root.glob("checkpoint_nexus*.tar.gz") if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    if not files:
        return {"exists": False}

    f = files[0]
    st = f.stat()
    return {
        "exists": True,
        "file": str(f),
        "size_bytes": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime).isoformat()
    }


@app.get("/promote/preflight")
def promote_preflight(x_api_key: str = Header(...)):
    verify(x_api_key)

    checks = {}

    try:
        subprocess.run(["python3", "-m", "py_compile", "/root/nexus100_20260419_143759/work/Servicios/nexus.py"], check=True, capture_output=True)
        checks["nexus_compile"] = True
    except:
        checks["nexus_compile"] = False

    try:
        subprocess.run(["python3", "-m", "py_compile", "/root/nexus100_20260419_143759/work/Controladores/api_control.py"], check=True, capture_output=True)
        checks["api_compile"] = True
    except:
        checks["api_compile"] = False

    try:
        latest = sorted(
            [f for f in Path("/root").glob("checkpoint_nexus*.tar.gz") if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        checks["checkpoint_exists"] = len(latest) > 0
    except:
        checks["checkpoint_exists"] = False

    checks["env_exists"] = Path("/root/.env.citafast").exists()
    checks["panel_exists"] = Path("/var/www/panel").exists()

    all_ok = all(checks.values())

    return {
        "all_ok": all_ok,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/cuentas/precheck")
def cuentas_precheck(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)

    detected = {}
    validation = None

    schedule_id = body.get("schedule_id")
    ivr_number = body.get("ivr_number")

    if body.get("email") and body.get("password"):
        validation = validate_ais({
            "email": body.get("email"),
            "password": body.get("password"),
            "country": body.get("country", "do"),
            "proxy": body.get("proxy")
        }, x_api_key)

        if validation.get("success") and validation.get("data"):
            first = validation["data"][0]
            detected = first
            schedule_id = schedule_id or first.get("schedule_id")
            ivr_number = ivr_number or first.get("ivr_number")

    dup = check_duplicate_identifiers(schedule_id, ivr_number)

    can_save = (dup is None) and (validation is None or bool(validation.get("success")))
    can_force_save = dup is None

    return {
        "success": True,
        "validation": validation,
        "detected": detected,
        "duplicate": dup,
        "can_save": can_save,
        "can_force_save": can_force_save,
        "recommended_status": "Activo" if can_save else "Pendiente de validación"
    }


def _build_whatsapp_booking_template(c):
    nombre = (c.get("nombre") or "Cliente").strip()
    fecha = (c.get("booked_date") or c.get("last_appointment_date") or "confirmada").strip()
    country = (c.get("country") or "do").upper()
    ivr = (c.get("ivr_number") or "").strip()
    sid = str(c.get("schedule_id") or "").strip()

    parts = [
        f"Hola {nombre},",
        "",
        "Te informamos que tu cita ha sido agendada correctamente.",
        f"📅 Fecha: {fecha}",
        f"🌎 País: {country}",
    ]
    if ivr:
        parts.append(f"🧾 IVR: {ivr}")
    if sid:
        parts.append(f"🔑 Schedule ID: {sid}")
    parts += [
        "",
        "Por favor, confirma tu pago pendiente para completar el cierre del proceso.",
        "Gracias por confiar en nosotros."
    ]
    return "\n".join(parts)


def _push_booking_outside_alert(title, message):
    try:
        req.post(
            "https://onesignal.com/api/v1/notifications",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Basic os_v2_app_bwm5bhd46vhdtegjlotocbkegltlpkj4ghluzrnvbvd46ds567qnpkqtg7r4bmnrr7ullomgxchxvv2y2dbj4sl7zixx6piqer7ck6i"
            },
            json={
                "app_id": "0d99d09c-7cf5-4e39-90c9-5ba6e1054432",
                "included_segments": ["All"],
                "headings": {"en": title},
                "contents": {"en": message},
                "url": "https://vps.citaflash.com/panel/"
            },
            timeout=10
        )
    except:
        pass


def _detect_external_booking_for_account(cuenta_id, x_api_key):
    current_rows = supabase.table("cuentas_citafast").select("*").eq("id", cuenta_id).execute().data or []
    if not current_rows:
        return {"success": False, "error": "Cuenta no encontrada"}

    before = current_rows[0]
    before_status = (before.get("status") or "").strip().lower()
    before_date = (before.get("last_appointment_date") or "").strip()
    before_booked_outside = bool(before.get("booked_outside") or False)

    sync_res = sync_cuenta(cuenta_id, x_api_key)
    if not sync_res.get("success"):
        return {"success": False, "error": sync_res.get("error", "sync_failed")}

    after_rows = supabase.table("cuentas_citafast").select("*").eq("id", cuenta_id).execute().data or []
    if not after_rows:
        return {"success": False, "error": "Cuenta no encontrada luego de sync"}

    after = after_rows[0]
    after_date = (after.get("last_appointment_date") or "").strip()
    after_status = (after.get("status") or "").strip().lower()

    # Detectar como "agendada fuera del bot":
    # - AIS ahora muestra una cita
    # - no estaba marcada como agendada por el sistema
    # - no estaba ya marcada como booked_outside
    detected = bool(
        after_date
        and before_status != "cita agendada"
        and after_status != "cita agendada"
        and not before_booked_outside
    )

    changed_date = bool(after_date and after_date != before_date)

    if detected or changed_date:
        updates = {
            "booked_outside": True,
            "booked_date": after_date or before_date or None,
            "status": "Agendada fuera del bot",
            "is_active": False,
            "updated_at": datetime.now().isoformat()
        }
        supabase.table("cuentas_citafast").update(updates).eq("id", cuenta_id).execute()

        try:
            supabase.table("nexus_trazas").insert({
                "cuenta_id": str(cuenta_id),
                "email": after.get("email") or "",
                "tipo": "warning",
                "mensaje": "Cuenta detectada como agendada fuera del bot",
                "datos": {
                    "before_status": before.get("status"),
                    "before_date": before_date,
                    "after_date": after_date,
                    "schedule_id": after.get("schedule_id"),
                    "ivr_number": after.get("ivr_number"),
                }
            }).execute()
        except:
            pass

        _push_booking_outside_alert(
            "Cuenta agendada fuera del bot",
            f"{after.get('email') or 'Cuenta'} fue detectada con cita en AIS fuera del flujo del bot."
        )

        after = supabase.table("cuentas_citafast").select("*").eq("id", cuenta_id).execute().data[0]
        return {
            "success": True,
            "detected": True,
            "booked_outside": True,
            "data": after
        }

    return {
        "success": True,
        "detected": False,
        "booked_outside": bool(after.get("booked_outside") or False),
        "data": after
    }


@app.post("/cuentas/{id}/detect-booked-outside")
def detect_booked_outside_single(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)
    return _detect_external_booking_for_account(id, x_api_key)


@app.post("/cuentas/detect-booked-outside/bulk")
async def detect_booked_outside_bulk(request: Request, x_api_key: str = Header(...)):
    verify(x_api_key)
    body = await request.json()
    limit = int(body.get("limit", 100))
    only_active = _truthy(body.get("only_active", True))

    q = supabase.table("cuentas_citafast").select("id,is_active,status").limit(limit)
    if only_active:
        q = q.eq("is_active", True)

    rows = q.execute().data or []
    results = []
    detected = 0

    for r in rows:
        # Saltar ya agendadas o ya marcadas fuera del bot
        status = (r.get("status") or "").strip().lower()
        if status in ("cita agendada", "agendada fuera del bot"):
            continue

        res = _detect_external_booking_for_account(r["id"], x_api_key)
        results.append({"id": r["id"], "result": res})
        if res.get("detected"):
            detected += 1

    return {
        "success": True,
        "checked": len(results),
        "detected_total": detected,
        "results": results
    }


@app.get("/cuentas/booked-outside/feed")
def cuentas_booked_outside_feed(x_api_key: str = Header(...), limit: int = 100):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select("*").eq("booked_outside", True).order("updated_at", desc=True).limit(limit).execute().data or []

    return {
        "total": len(rows),
        "items": rows
    }


@app.get("/cuentas/{id}/booking-modal")
def cuentas_booking_modal(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select("*").eq("id", id).execute().data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    c = rows[0]
    return {
        "id": c.get("id"),
        "email": c.get("email"),
        "nombre": c.get("nombre"),
        "country": c.get("country"),
        "status": c.get("status"),
        "schedule_id": c.get("schedule_id"),
        "ivr_number": c.get("ivr_number"),
        "total_personas": c.get("total_personas"),
        "last_appointment_date": c.get("last_appointment_date"),
        "booked_date": c.get("booked_date"),
        "booked_outside": bool(c.get("booked_outside") or False),
        "updated_at": c.get("updated_at")
    }


@app.get("/cuentas/{id}/whatsapp-template")
def cuentas_whatsapp_template(id: int, x_api_key: str = Header(...)):
    verify(x_api_key)

    rows = supabase.table("cuentas_citafast").select("*").eq("id", id).execute().data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    c = rows[0]
    text = _build_whatsapp_booking_template(c)

    return {
        "id": c.get("id"),
        "email": c.get("email"),
        "nombre": c.get("nombre"),
        "status": c.get("status"),
        "booked_outside": bool(c.get("booked_outside") or False),
        "template_text": text,
        "copy_text": text
    }



@app.post("/nexus/speed")
def set_nexus_speed(body: dict, x_api_key: str = Header(...)):
    verify(x_api_key)
    modo = body.get("modo", "normal")
    delays = {
        "bajo": 20.0,
        "medio": 10.0,
        "alto": 5.0,
        "ultra": 0.5,
        "mega": 0.2
    }
    delay = delays.get(modo, 1.2)
    import subprocess
    subprocess.run(["bash","-c",f"echo 'NEXUS_DELAY={delay}' > /tmp/nexus_speed.env"])
    os.environ["NEXUS_DELAY"] = str(delay)
    return {"ok": True, "modo": modo, "delay": delay}

@app.get("/nexus/speed")
def get_nexus_speed(x_api_key: str = Header(...)):
    verify(x_api_key)
    delay = os.getenv("NEXUS_DELAY","1.2")
    return {"delay": delay}

@app.post("/maintenance/unblock-expired")
def maintenance_unblock_expired(x_api_key: str = Header(...)):
    verify(x_api_key)
    return normalize_expired_ais_blocks()
