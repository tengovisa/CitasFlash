#!/bin/bash
LOG="/var/log/miercoles_ultra.log"
API="https://vps.citaflash.com"
KEY="CitasFlash2026Servicio2"

echo "$(date) — ↩️ VOLVIENDO A MODO NORMAL" >> $LOG

# Velocidad normal
curl -s -X POST "$API/runtime/config" \
  -H "x-api-key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds":1.5,"speed_mode":"normal"}' >> $LOG

# Notificar
curl -s -X POST \
  "https://api.telegram.org/bot8612004045:AAGFmqfUsmefl0YoR2PGTyZd26YDvZQm0Zo/sendMessage" \
  -d "chat_id=1193245321&text=↩️ Volviendo a modo NORMAL%0A🕐 $(date '+%H:%M')"

echo "$(date) — ✅ Normal restaurado" >> $LOG
