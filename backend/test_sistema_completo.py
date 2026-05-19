#!/usr/bin/env python3
"""TEST GLOBAL CITASFLASH — 03/05/2026"""
import requests, json, time, subprocess
from datetime import datetime

API = "https://vps.citaflash.com"
KEY = "CitasFlash2026Servicio2"
H = {"x-api-key": KEY, "Content-Type": "application/json"}
ok = []; fail = []; warn = []

def t(nombre, resultado, detalle=""):
    if resultado == "ok":   ok.append(nombre);   print(f"  ✅ {nombre} {detalle}")
    elif resultado == "warn": warn.append(nombre); print(f"  ⚠️  {nombre} {detalle}")
    else:                   fail.append(nombre); print(f"  ❌ {nombre} {detalle}")

def get(path):
    try: r=requests.get(API+path,headers=H,timeout=10); return r.json() if r.ok else None
    except: return None

def post(path, body={}):
    try: r=requests.post(API+path,headers=H,json=body,timeout=15); return r.json() if r.ok else None
    except: return None

def put(path, body={}):
    try: r=requests.put(API+path,headers=H,json=body,timeout=10); return r.json() if r.ok else None
    except: return None

print("\n" + "="*60)
print("   TEST GLOBAL CITASFLASH NEXUS — " + datetime.now().strftime("%d/%m/%Y %H:%M"))
print("="*60)

# ── 1. PANEL ──────────────────────────────────────────────
print("\n[1] PANEL WEB")
import urllib.request
try:
    code = urllib.request.urlopen("https://vps.citaflash.com/panel/",timeout=10).getcode()
    t("Panel carga", "ok" if code==200 else "fail", f"HTTP {code}")
except Exception as e:
    t("Panel carga", "fail", str(e)[:40])

# ── 2. API CORE ──────────────────────────────────────────
print("\n[2] API CORE")
ping = get("/ping")
t("API /ping", "ok" if ping else "fail", str(ping))

mon = get("/monitor")
t("Monitor responde", "ok" if mon else "fail")
if mon:
    t("Bot activo", "ok" if mon.get("bot")=="active" else "fail", mon.get("bot","—"))
    t("dry_run OFF", "ok" if not mon.get("runtime",{}).get("dry_run") else "fail",
      str(mon.get("runtime",{}).get("dry_run")))
    t("CPU normal", "ok" if (mon.get("cpu") or 0)<80 else "warn", str(mon.get("cpu","—"))+"%")
    t("RAM disponible", "ok" if (mon.get("ram",{}).get("available") or 0)>2 else "warn",
      str(mon.get("ram",{}).get("available","—"))+"GB")
    t("Proxies libres", "ok" if (mon.get("proxies",{}).get("free") or 0)>0 else "fail",
      str(mon.get("proxies",{}).get("free","—"))+" libres")

# ── 3. CUENTAS ───────────────────────────────────────────
print("\n[3] CUENTAS")
cuentas = get("/cuentas")
lista = cuentas if isinstance(cuentas,list) else (cuentas or {}).get("cuentas",[])
t("GET /cuentas", "ok" if lista else "fail", f"{len(lista)} cuentas")
t("Cuentas con login OK", "ok" if sum(1 for c in lista if not c.get("last_login_fail"))>0 else "warn",
  f"{sum(1 for c in lista if not c.get('last_login_fail'))}/{len(lista)}")
t("Cuentas con proxy", "ok" if sum(1 for c in lista if c.get("proxies"))>0 else "warn",
  f"{sum(1 for c in lista if c.get('proxies'))}/{len(lista)}")
t("Ninguna bloqueada AIS", "ok" if sum(1 for c in lista if "Bloqueada" in (c.get("status") or ""))==0 else "warn",
  f"{sum(1 for c in lista if 'Bloqueada' in (c.get('status') or ''))} bloqueadas")

# ── 4. TEST PLAY/STOP ─────────────────────────────────────
print("\n[4] PLAY / STOP (cuenta 188)")
cid = 188
r1 = put(f"/cuentas/{cid}", {"is_active":True,"status":"En proceso"})
t("PUT activar cuenta", "ok" if r1 and r1.get("is_active") else "fail")
time.sleep(12)
r2 = put(f"/cuentas/{cid}", {"is_active":False,"status":"Pausado"})
t("PUT pausar cuenta", "ok" if r2 and not r2.get("is_active") else "fail")
time.sleep(18)
# Verificar que el hilo se detuvo
log = subprocess.run(["grep","desactivada","/root/log_nexus.txt"],capture_output=True,text=True)
t("Hilo detenido en <15s", "ok" if "desactivada" in log.stdout else "warn",
  "⚠️ Verificar log manual" if "desactivada" not in log.stdout else "")

# ── 5. PROXIES ────────────────────────────────────────────
print("\n[5] PROXIES")
pxs = get("/proxies")
plist = pxs if isinstance(pxs,list) else (pxs or {}).get("proxies",[])
t("GET /proxies", "ok" if plist else "fail", f"{len(plist)} proxies")
stats = get("/proxies/stats")
t("GET /proxies/stats", "ok" if stats else "fail",
  f"free:{stats.get('residential',{}).get('free','?')}" if stats else "—")
t("Sin proxies dead", "ok" if (stats or {}).get("residential",{}).get("dead",0)==0 else "warn")

# ── 6. VALIDATE AIS ──────────────────────────────────────
print("\n[6] VALIDATE AIS")
c1 = lista[0] if lista else {}
if c1:
    rv = post("/validate-ais-v2", {"email":c1.get("email"),"password":c1.get("password")})
    t("validate-ais-v2", "ok" if rv and rv.get("success") else "warn",
      f"cita: {rv.get('data',[{}])[0].get('cita_actual','—')}" if rv and rv.get("success") else str(rv)[:50])
else:
    t("validate-ais-v2", "warn", "sin cuentas para probar")

# ── 7. ENDPOINTS CRÍTICOS ────────────────────────────────
print("\n[7] ENDPOINTS")
eps = [("/monitor","GET"),("/cuentas","GET"),("/proxies","GET"),
       ("/logs/tail-json","GET"),("/proxies/stats","GET"),
       ("/runtime/config","GET"),("/cmd/nexus/start","POST"),
       ("/validate-ais-v2","POST")]
for ep,method in eps:
    try:
        if method=="GET": r=requests.get(API+ep,headers=H,timeout=8)
        else: r=requests.post(API+ep,headers=H,json={},timeout=8)
        t(f"{method} {ep}", "ok" if r.status_code in [200,422] else "warn", f"HTTP {r.status_code}")
    except Exception as e:
        t(f"{method} {ep}", "fail", str(e)[:30])

# ── 8. LOG EN TIEMPO REAL ────────────────────────────────
print("\n[8] LOG")
log_api = get("/logs/tail-json?lines=10")
t("GET logs/tail-json", "ok" if log_api and log_api.get("items") else "fail",
  f"{log_api.get('total',0)} items" if log_api else "—")
if log_api and log_api.get("items"):
    ultimo = log_api["items"][-1]
    age_ts = ultimo.get("ts","")
    t("Log tiene datos frescos", "ok" if "2026-05" in age_ts else "warn", age_ts[:16])

# ── 9. NEXUS CMD ─────────────────────────────────────────
print("\n[9] NEXUS CONTROL")
rc = get("/runtime/config")
t("GET runtime/config", "ok" if rc else "fail")
if rc:
    t("dry_run en config", "ok" if not rc.get("dry_run") else "fail", str(rc.get("dry_run")))

# ── 10. SYSTEMD ──────────────────────────────────────────
print("\n[10] SYSTEMD")
st = subprocess.run(["systemctl","is-active","nexus"],capture_output=True,text=True)
t("nexus.service activo", "ok" if "active" in st.stdout else "fail", st.stdout.strip())
restart_ok = subprocess.run(["grep","Restart=always","/etc/systemd/system/nexus.service"],capture_output=True)
t("Restart=always configurado", "ok" if restart_ok.returncode==0 else "fail")

# ── RESUMEN ──────────────────────────────────────────────
print("\n" + "="*60)
total = len(ok)+len(fail)+len(warn)
pct = round((len(ok)/total)*100) if total>0 else 0
print(f"   RESULTADO: {len(ok)}/{total} tests OK — {pct}%")
print(f"   ✅ OK: {len(ok)}  ⚠️ WARN: {len(warn)}  ❌ FAIL: {len(fail)}")
if fail: print(f"   CRÍTICO: {', '.join(fail)}")
if warn: print(f"   REVISAR: {', '.join(warn)}")
print("="*60 + "\n")
