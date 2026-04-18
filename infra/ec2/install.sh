#!/bin/bash
set -e

# Install system deps (Amazon Linux 2023 — same as Lambda base image)
dnf install -y \
    python3.12 python3.12-pip git \
    atk at-spi2-atk cups-libs \
    libXcomposite libXdamage libXfixes libXrandr \
    libgbm libxkbcommon nss pango alsa-lib \
    xorg-x11-fonts-Type1

# App directory
mkdir -p /var/app
cd /var/app

# Clone or pull repo (assumes SSH key already on instance)
if [ -d ".git" ]; then
    git pull
else
    git clone git@github.com:AndreiErofeev/termin_checker.git .
fi

# Python deps
python3.12 -m pip install -r requirements.txt boto3

# Install Chromium for Playwright
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
playwright install chromium

# Copy and enable systemd service
cp infra/ec2/termin-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable termin-bot
systemctl restart termin-bot

echo "Done. Check status: systemctl status termin-bot"
