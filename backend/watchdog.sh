#!/bin/bash
LOG="/var/log/watchdog.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

check_service(){
    local name=$1
    local check_cmd=$2
    if ! eval "$check_cmd" > /dev/null 2>&1; then
        echo "[$DATE] ❌ $name CAÍDO — reiniciando..." >> $LOG
        systemctl restart $name
        sleep 5
        if eval "$check_cmd" > /dev/null 2>&1; then
            echo "[$DATE] ✅ $name recuperado" >> $LOG
        else
            echo "[$DATE] 🚨 $name NO ARRANCÓ" >> $LOG
        fi
    fi
}

# Verificar cada servicio
check_service "tengovisa-api" "curl -sf http://localhost:8001/health -H 'x-api-key: TengoVisa2026API'"
check_service "apivps" "curl -sf http://localhost:8000/ping -H 'x-api-key: CitaFast2026Bot2'"
check_service "nginx" "nginx -t"
check_service "nexus" "systemctl is-active nexus"

# Verificar puertos
if ! ss -tlnp | grep -q "8001"; then
    echo "[$DATE] 🚨 Puerto 8001 no escucha — reiniciando tengovisa-api" >> $LOG
    systemctl restart tengovisa-api
fi
if ! ss -tlnp | grep -q "8000"; then
    echo "[$DATE] 🚨 Puerto 8000 no escucha — reiniciando apivps" >> $LOG
    systemctl restart apivps
fi

# Limpiar log si muy grande
[ $(stat -c%s $LOG 2>/dev/null || echo 0) -gt 5242880 ] && tail -500 $LOG > /tmp/wdtmp && mv /tmp/wdtmp $LOG
