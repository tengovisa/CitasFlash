#!/bin/bash
# Auto-activación miércoles 7:45am AST

LOG="/var/log/miercoles_ultra.log"
API="https://vps.citaflash.com"
KEY="CitasFlash2026Servicio2"

echo "$(date) — 🚀 INICIANDO MODO MIÉRCOLES ULTRA" >> $LOG

# 1. Cambiar a modo ULTRA
curl -s -X POST "$API/runtime/config" \
  -H "x-api-key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds":0.5,"speed_mode":"ultra"}' >> $LOG

echo "" >> $LOG
echo "$(date) — ⚡ Speed: ULTRA 0.5s" >> $LOG

# 2. Activar TODAS las cuentas con schedule_id
python3 << 'PYEOF'
import requests, json

API = "https://vps.citaflash.com"
H = {"x-api-key":"CitasFlash2026Servicio2","Content-Type":"application/json"}

l = requests.get(f"{API}/cuentas", headers=H).json()
l = l if isinstance(l,list) else []

activadas = 0
for c in l:
    if c.get("schedule_id"):
        r = requests.put(f"{API}/cuentas/{c['id']}", headers=H,
            json={"is_active":True,"status":"En proceso"})
        activadas += 1
        print(f"✅ Activada: {c['email']}")

print(f"Total: {activadas} cuentas activas")
PYEOF

# 3. Notificar Telegram
curl -s -X POST \
  "https://api.telegram.org/bot8612004045:AAGFmqfUsmefl0YoR2PGTyZd26YDvZQm0Zo/sendMessage" \
  -d "chat_id=1193245321&text=🚀 MIÉRCOLES ULTRA ACTIVADO%0A⚡ 0.5s delay%0A✅ Todas las cuentas corriendo%0A🕐 $(date '+%H:%M')"

echo "$(date) — ✅ Todo activado" >> $LOG
