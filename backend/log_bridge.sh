#!/bin/bash
while true; do
  journalctl -u nexus --no-pager -n 300 --output=short 2>/dev/null | \
    grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+ \[.*' > /root/log_nexus.txt
  sleep 5
done
