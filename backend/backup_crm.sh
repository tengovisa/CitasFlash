#!/bin/bash
FECHA=$(date +%Y%m%d_%H%M)
BDIR="/root/backups"
mkdir -p $BDIR

# API
cp /root/tengovisa_api.py $BDIR/api_$FECHA.py

# Frontend
tar -czf $BDIR/crm_frontend_$FECHA.tar.gz /var/www/crm/ 2>/dev/null

# Limpiar backups > 7 días
find $BDIR -name "*.py" -mtime +7 -delete
find $BDIR -name "*.tar.gz" -mtime +7 -delete
find $BDIR -name "*.html" -mtime +7 -delete

echo "[$FECHA] Backup OK"
