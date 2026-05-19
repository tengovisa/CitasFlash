#!/bin/bash
LOG="/root/log_watchdog.txt"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
log() { echo "[$DATE] $1" >> $LOG; }

log "🔄 Iniciando auto-update..."
apt-get update -qq && apt-get upgrade -y -qq --only-upgrade 2>/dev/null
log "✅ Sistema actualizado"
pip install --upgrade supabase fastapi uvicorn requests python-dotenv firebase-admin --break-system-packages -q 2>/dev/null
log "✅ Librerias Python actualizadas"
echo "Skipping systemd restart — managed manually"
sleep 5
log "✅ Auto-update completado — Nexus:$(systemctl is-active nexus) API:$(systemctl is-active citasflash-api)"
