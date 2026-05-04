#!/usr/bin/env bash
# First-time VPS setup for EMLMS on Ubuntu 24.04
# Run as root: bash server_setup.sh YOUR_DOMAIN
set -euo pipefail

DOMAIN="${1:?Usage: $0 your.domain.com}"
APP_DIR="/var/www/emlms"
PYTHON_VERSION="3.12"

echo "==> Updating system..."
apt-get update && apt-get upgrade -y

echo "==> Installing system packages..."
apt-get install -y \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev \
    python3-pip build-essential \
    nginx certbot python3-certbot-nginx \
    postgresql postgresql-contrib \
    redis-server \
    git curl \
    libpq-dev \
    libmagic1 \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
    gir1.2-pango-1.0 libcairo2 libffi-dev \
    supervisor

echo "==> Creating application user & directory..."
useradd -m -s /bin/bash emlms 2>/dev/null || true
mkdir -p "$APP_DIR"
chown emlms:www-data "$APP_DIR"

echo "==> Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE USER emlms_user WITH PASSWORD 'CHANGE_ME_STRONG_PASSWORD';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE emlms_db OWNER emlms_user;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE emlms_db TO emlms_user;" 2>/dev/null || true

echo "==> Enabling Redis..."
systemctl enable redis-server
systemctl start redis-server

echo "==> Creating log directory..."
mkdir -p /var/log/emlms /var/run/emlms
chown www-data:www-data /var/log/emlms /var/run/emlms

echo "==> Cloning repo (update remote URL if needed)..."
if [ ! -d "$APP_DIR/.git" ]; then
    git clone https://github.com/YOUR_USER/emlms.git "$APP_DIR"
fi
chown -R www-data:www-data "$APP_DIR"

echo "==> Setting up Python virtual environment..."
sudo -u www-data python${PYTHON_VERSION} -m venv "$APP_DIR/venv"
sudo -u www-data "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u www-data "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements/production.txt"

echo "==> Installing systemd services..."
cp "$APP_DIR/deploy/emlms.socket"         /etc/systemd/system/
cp "$APP_DIR/deploy/emlms.service"         /etc/systemd/system/
cp "$APP_DIR/deploy/emlms-celery.service"  /etc/systemd/system/
cp "$APP_DIR/deploy/emlms-celerybeat.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable emlms.socket emlms.service emlms-celery.service emlms-celerybeat.service

echo "==> Installing Nginx config..."
sed "s/YOUR_DOMAIN_HERE/$DOMAIN/g" "$APP_DIR/deploy/nginx.conf" \
    > /etc/nginx/sites-available/emlms
ln -sf /etc/nginx/sites-available/emlms /etc/nginx/sites-enabled/emlms
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "==> Obtaining SSL certificate..."
certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m admin@"$DOMAIN"

echo "==> Creating static/media dirs..."
mkdir -p "$APP_DIR/staticfiles" "$APP_DIR/media"
chown www-data:www-data "$APP_DIR/staticfiles" "$APP_DIR/media"

echo ""
echo "============================================================"
echo " Server setup complete!"
echo " Next steps:"
echo "   1. Copy your .env file to $APP_DIR/.env"
echo "   2. Run migrations:  cd $APP_DIR && venv/bin/python manage.py migrate"
echo "   3. Collect static:  venv/bin/python manage.py collectstatic --noinput"
echo "   4. Create superuser: venv/bin/python manage.py createsuperuser"
echo "   5. Start services:  systemctl start emlms.socket emlms-celery emlms-celerybeat"
echo "============================================================"
