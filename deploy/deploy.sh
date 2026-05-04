#!/usr/bin/env bash
# EMLMS deployment script — run as www-data or with sudo
# Usage: ./deploy/deploy.sh
set -euo pipefail

APP_DIR="/var/www/emlms"
VENV="$APP_DIR/venv"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"

echo "==> Pulling latest code..."
cd "$APP_DIR"
git pull origin main

echo "==> Installing/updating Python dependencies..."
$PIP install -r requirements/production.txt --quiet

echo "==> Collecting static files..."
DJANGO_SETTINGS_MODULE=emlms.settings.production $PYTHON manage.py collectstatic --noinput --verbosity=0

echo "==> Running database migrations..."
DJANGO_SETTINGS_MODULE=emlms.settings.production $PYTHON manage.py migrate --noinput

echo "==> Running system checks..."
DJANGO_SETTINGS_MODULE=emlms.settings.production $PYTHON manage.py check --deploy

echo "==> Restarting Gunicorn..."
sudo systemctl restart emlms.socket emlms.service

echo "==> Restarting Celery workers..."
sudo systemctl restart emlms-celery.service emlms-celerybeat.service

echo "==> Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "Deploy complete."
sudo systemctl status emlms.service --no-pager -l
