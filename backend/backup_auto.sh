#!/bin/bash
DATE=$(date +%Y%m%d%H%M)
cp /var/www/nexus/index.html /var/www/nexus/index.html.bak.$DATE
cp /root/nexus.py /root/nexus.py.bak.$DATE
# Mantener solo últimos 5 backups
ls -t /var/www/nexus/index.html.bak.* | tail -n +6 | xargs rm -f 2>/dev/null
ls -t /root/nexus.py.bak.* | tail -n +6 | xargs rm -f 2>/dev/null
