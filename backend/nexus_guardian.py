#!/usr/bin/env python3
"""Guardian — solo reactiva cuentas que ESTABAN activas y se cayeron"""
import requests, json, os
from datetime import datetime

API = "https://vps.citaflash.com"
H = {"x-api-key":"CitasFlash2026Servicio2","Content-Type":"application/json"}
CACHE = "/tmp/nexus_guardian_cache.json"

# Cargar cache de cuentas que deben estar activas
try:
    cache = json.load(open(CACHE))
except:
    cache = {}

l = requests.get(f"{API}/cuentas", headers=H).json()
l = l if isinstance(l,list) else []

for c in l:
    cid = str(c['id'])
    activa = c.get('is_active', False)
    
    # Si está activa — guardar en cache
    if activa:
        cache[cid] = True
    
    # Si estaba activa (en cache) pero se cayó — reactivar
    if cache.get(cid) and not activa and c.get('schedule_id'):
        r = requests.put(f"{API}/cuentas/{c['id']}", headers=H,
            json={"is_active":True,"status":"En proceso"})
        print(f"{datetime.now().strftime('%H:%M')} — Reactivada: {c['email']}")

json.dump(cache, open(CACHE,'w'))
