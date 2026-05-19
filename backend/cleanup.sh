#!/bin/bash
# Limpiar logs viejos (más de 7 días)
find /root -name "*.log" -mtime +7 -delete
# Limpiar log del servicio si supera 50MB
if [ $(stat -c%s /root/log_nexus.txt 2>/dev/null || echo 0) -gt 52428800 ]; then
    tail -5000 /root/log_nexus.txt > /tmp/log_tmp.txt
    mv /tmp/log_tmp.txt /root/log_nexus.txt
fi
# Limpiar cache del sistema
sync && echo 3 > /proc/sys/vm/drop_caches
# Limpiar pycache
find /root -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "✅ Limpieza completada $(date)"
