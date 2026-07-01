#!/usr/bin/env bash
# Run this on a fresh Ubuntu Oracle Cloud VM after the project files are already at
# /opt/social_media_auto_upload (see README "Deploying to Oracle Cloud" section).
set -euo pipefail

APP_DIR=/opt/social_media_auto_upload

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip ffmpeg

cd "$APP_DIR"

if [ ! -d venv ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
    echo "ERROR: $APP_DIR/.env not found. Copy your local .env here before continuing."
    exit 1
fi

sudo cp deploy/social-media-auto-upload.service /etc/systemd/system/social-media-auto-upload.service
sudo systemctl daemon-reload
sudo systemctl enable social-media-auto-upload
sudo systemctl restart social-media-auto-upload

echo "Done. Check status with: sudo systemctl status social-media-auto-upload"
echo "Check logs with: sudo journalctl -u social-media-auto-upload -f"
