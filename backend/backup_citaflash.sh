#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
DEST="/root/backups/backup_$DATE"
mkdir -p $DEST
cp /var/www/panel/index.html $DEST/
cp /root/nexus.py $DEST/
cp /root/api_control.py $DEST/
cp /root/.env.citafast $DEST/
# Borrar backups con más de 7 días
find /root/backups -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
echo "✅ Backup $DATE completado"
