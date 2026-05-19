#!/bin/bash
# Nexus Auto-Maintenance — corre cada hora
LOG="/var/log/nexus_maintenance.log"
echo "=== MAINTENANCE $(date '+%d/%m/%Y %H:%M') ===" >> $LOG

# 1. Verificar que nexus está corriendo
if ! systemctl is-active --quiet nexus; then
    echo "NEXUS CAÍDO — reiniciando" >> $LOG
    systemctl restart nexus
    sleep 10
fi

# 2. Verificar procesos duplicados
PROCS=$(ps aux | grep nexus.py | grep -v grep | wc -l)
if [ "$PROCS" -gt 1 ]; then
    echo "DUPLICADOS ($PROCS) — limpiando" >> $LOG
    pkill -f nexus.py
    sleep 3
    systemctl restart nexus
fi

# 3. Reactivar cuentas con sesión inválida (falsos positivos watchdog)
python3 -c "
import os; from dotenv import load_dotenv; load_dotenv('/root/.env.citafast')
from supabase import create_client
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
PROXIES = 'axihbvupdatacenter:ng8m7kbc1met@184.174.44.59:6485,axihbvupdatacenter:ng8m7kbc1met@149.57.85.240:6208,axihbvupdatacenter:ng8m7kbc1met@172.121.235.210:8365'
r = sb.table('cuentas_citafast').select('id,status').execute()
for c in r.data:
    s = c.get('status','')
    if any(x in (s or '') for x in ['Sesión inválida','Error proxy','CSRF','Bloqueo desconocido']):
        sb.table('cuentas_citafast').update({'is_active':False,'status':'Pendiente de revalidación'}).eq('id',c['id']).execute()
r2 = sb.table('cuentas_citafast').select('id').eq('is_active',True).execute()
print(f'Activas: {len(r2.data)}')
" >> $LOG 2>&1

# 4. Backup automático diario (solo 1 por día)
FECHA=$(date +%Y%m%d)
if [ ! -f "/root/backup/nexus_AUTO_${FECHA}.py" ]; then
    cp /root/nexus.py "/root/backup/nexus_AUTO_${FECHA}.py"
    echo "Backup diario creado" >> $LOG
    # Limpiar backups viejos (mantener últimos 7)
    ls -t /root/backup/nexus_AUTO_*.py | tail -n +8 | xargs -r rm
fi

echo "Activas: $(python3 -c "
import os; from dotenv import load_dotenv; load_dotenv('/root/.env.citafast')
from supabase import create_client
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
r = sb.table('cuentas_citafast').select('id').eq('is_active',True).execute()
print(len(r.data))
" 2>/dev/null)" >> $LOG

echo "=== FIN ===" >> $LOG
