#!/bin/bash
DATE=$(date +%Y%m%d)
DIR="/root/backup/$DATE"
mkdir -p $DIR
cp /var/www/crm/index.html $DIR/crm_auto.html 2>/dev/null
cp /var/www/crm/extras.js $DIR/extras_auto.js 2>/dev/null
cp /root/tengovisa_api.py $DIR/api_auto.py 2>/dev/null
cp /root/api_control.py $DIR/api_control_auto.py 2>/dev/null
cp /var/www/nexus/index.html $DIR/nexus_auto.html 2>/dev/null
# Mantener solo últimos 7 días
find /root/backup -maxdepth 1 -type d -mtime +7 -exec rm -rf {} + 2>/dev/null
echo "$(date) ✅ Backup diario completado" >> /var/log/backup.log
