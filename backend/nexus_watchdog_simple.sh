#!/bin/bash
# Watchdog simple — revisar cada 60s
while true; do
  if ! systemctl is-active --quiet nexus; then
    echo "$(date) — nexus caído, reiniciando..." >> /var/log/nexus_watchdog_simple.log
    systemctl start nexus
  fi
  sleep 60
done
