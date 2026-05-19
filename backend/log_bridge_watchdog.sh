#!/bin/bash
while true; do
  if ! pgrep -f "log_bridge.sh" > /dev/null; then
    echo "$(date) — log_bridge caído, reiniciando..." >> /var/log/log_bridge_watchdog.log
    nohup /root/log_bridge.sh > /dev/null 2>&1 &
  fi
  sleep 30
done
