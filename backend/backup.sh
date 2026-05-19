#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
BDIR="/root/backups/$DATE"
mkdir -p $BDIR

# Backup API
cp /root/api_control.py $BDIR/api_control.py

# Backup panel
cp /var/www/panel/index.html $BDIR/index.html
cp /var/www/panel/activate.html $BDIR/activate.html 2>/dev/null

# Backup servicio
cp /root/nexus.py $BDIR/nexus.py

# Backup nginx config
cp /etc/nginx/sites-available/nexus $BDIR/nginx_nexus.conf

# Backup env
cp /root/.env.nexus $BDIR/env_nexus

# Compress
tar -czf /root/backups/backup_$DATE.tar.gz $BDIR/
rm -rf $BDIR

# Keep only last 7 backups
find /root/backups/ -name "*.tar.gz" -mtime +10 -delete

echo "Backup $DATE completado"
