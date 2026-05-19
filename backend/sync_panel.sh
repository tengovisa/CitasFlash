#!/bin/bash
if [ ! -L /var/www/panel/index.html ]; then
    rm -f /var/www/panel/index.html
    ln -s /var/www/nexus/index.html /var/www/panel/index.html
    nginx -s reload
    echo "$(date) — symlink restaurado" >> /var/log/sync_panel.log
fi
