#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./scripts/install_services.sh"
    exit 1
fi

for svc in otodombot-backend.service otodombot-scraper.service otodombot-frontend.service; do
    sed "s|__WORKDIR__|$REPO_DIR|g" "$REPO_DIR/scripts/systemd/$svc" > "/etc/systemd/system/$svc"
    echo "Installed /etc/systemd/system/$svc"
done

systemctl daemon-reload

for svc in otodombot-backend.service otodombot-scraper.service otodombot-frontend.service; do
    systemctl enable "$svc"
    systemctl restart "$svc" || true
done

echo "Services installed and enabled."
