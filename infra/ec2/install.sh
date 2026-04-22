#!/bin/bash
set -e

# Install system deps (Amazon Linux 2023 — same as Lambda base image)
dnf install -y \
    python3.12 python3.12-pip git cronie \
    atk at-spi2-atk cups-libs \
    libXcomposite libXdamage libXfixes libXrandr \
    libgbm libxkbcommon nss pango alsa-lib \
    xorg-x11-fonts-Type1
systemctl enable --now crond

# App directory
mkdir -p /var/app
cd /var/app

# Clone or pull repo (public repo — no SSH key needed)
if [ -d ".git" ]; then
    git pull origin development
else
    git clone https://github.com/AndreiErofeev/termin_checker.git .
    git checkout development
fi

# Python deps
python3.12 -m pip install -r requirements.txt

# Install Chromium for Playwright — install as root but make world-readable
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
playwright install chromium
chmod -R a+rX /ms-playwright

# Copy and enable systemd service
cp infra/ec2/termin-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable termin-bot
systemctl restart termin-bot

# Hourly S3 backup of SQLite DB (requires S3_BUCKET in /var/app/.env)
if [ ! -f /var/app/.env ]; then
    echo "WARNING: /var/app/.env not found — skipping S3 backup cron setup"
else
    S3_BUCKET=$(grep '^S3_BUCKET=' /var/app/.env | cut -d= -f2 | tr -d '[:space:]')
    if [ -z "$S3_BUCKET" ]; then
        echo "WARNING: S3_BUCKET not set in .env — skipping S3 backup cron setup"
    else
        CRON_JOB="0 * * * * aws s3 cp /var/app/termin.db s3://${S3_BUCKET}/backups/termin.db --region eu-west-1 >> /var/log/termin-backup.log 2>&1"
        (crontab -l 2>/dev/null | grep -v 'termin.db'; echo "$CRON_JOB") | crontab -
        echo "S3 backup cron installed for bucket: $S3_BUCKET"
    fi
fi

echo "Done. Check status: systemctl status termin-bot"
