#!/usr/bin/env python3
from curl_cffi import requests
from bs4 import BeautifulSoup
import re

email = "toledocuestayasociados@gmail.com"
password = "TU_CONTRASEÑA"  # Cámbiala o la leeremos de .env

session = requests.Session(impersonate="chrome120")

# 1. Login completo
print("1. Login...")
r1 = session.get("https://ais.usvisa-info.com/en-do/niv/users/sign_in", timeout=15)
csrf = BeautifulSoup(r1.text, "html.parser").find("meta", {"name": "csrf-token"})["content"]

r2 = session.post("https://ais.usvisa-info.com/en-do/niv/users/sign_in",
    data={"user[email]": email, "user[password]": password, "policy_confirmed": "1", "commit": "Sign In"},
    headers={"X-CSRF-Token": csrf}, timeout=15)
print(f"   Login status: {r2.status_code}")

# 2. Ver qué URLs están disponibles en el perfil
print("\n2. Analizando perfil...")
r3 = session.get("https://ais.usvisa-info.com/en-do/niv", timeout=15)
print(f"   Status: {r3.status_code}")

# Buscar schedule_ids en el HTML
matches = re.findall(r'/schedule/(\d+)/', r3.text)
print(f"   Schedule IDs encontrados en HTML: {matches}")

# Buscar links a citas
links = re.findall(r'href="([^"]+appointment[^"]+)"', r3.text)
print(f"   Links de appointment: {links[:3]}")

# 3. Probar diferentes facility_id
print("\n3. Probando facility_id...")
facility_ids = [138, 112, 108, 105, 110]
for fid in facility_ids:
    url = f"https://ais.usvisa-info.com/en-do/niv/schedule/73940424/appointment/days/{fid}.json"
    r = session.get(url, timeout=10)
    print(f"   facility_id {fid}: {r.status_code} → {r.text[:80] if r.status_code!=200 else len(r.json())} fechas")

# 4. Verificar si hay una cita activa
print("\n4. Buscando cita actual...")
r4 = session.get("https://ais.usvisa-info.com/en-do/niv/schedule/73940424/appointment", timeout=15)
if "Reschedule" in r4.text or "Cancel" in r4.text:
    print("   ✅ Hay una cita activa (se puede reagendar)")
elif "Schedule" in r4.text:
    print("   ⚠️ No hay cita activa (hay que agendar primera cita)")
else:
    print(f"   Status: {r4.status_code} - Posiblemente sin cita")
