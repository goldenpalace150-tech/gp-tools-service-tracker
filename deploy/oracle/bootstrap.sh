#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/goldenpalace150-tech/gp-tools-service-tracker.git"
APP_DIR="/opt/gp-tools-service-tracker"
APP_USER="ubuntu"
APP_PORT="8000"
ENV_FILE="/etc/golden-palace.env"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script with sudo/root."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx curl

if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" fetch origin main
  git -C "$APP_DIR" reset --hard origin/main
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

if [ ! -d "$APP_DIR/.venv" ]; then
  sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
fi
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip wheel
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'EOF'
# Golden Palace production environment.
# Add GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS here
# before using TV write actions such as manual collection close.
TV_CACHE_TTL_SECONDS=15
REMARKS_CACHE_TTL_SECONDS=60
EOF
  chmod 600 "$ENV_FILE"
fi

cat > /etc/systemd/system/golden-palace.service <<EOF
[Unit]
Description=Golden Palace Tools/Service Tracker API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=-$ENV_FILE
ExecStart=$APP_DIR/.venv/bin/gunicorn --workers 2 --threads 4 --timeout 120 --bind 127.0.0.1:$APP_PORT flask_app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/local/sbin/golden-palace-update <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/gp-tools-service-tracker"
APP_USER="ubuntu"
OLD="$(git -C "$APP_DIR" rev-parse HEAD)"
git -C "$APP_DIR" fetch origin main
NEW="$(git -C "$APP_DIR" rev-parse origin/main)"
if [ "$OLD" = "$NEW" ]; then
  exit 0
fi
git -C "$APP_DIR" reset --hard origin/main
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
systemctl restart golden-palace.service
EOF
chmod 755 /usr/local/sbin/golden-palace-update

cat > /etc/systemd/system/golden-palace-update.service <<'EOF'
[Unit]
Description=Update Golden Palace from GitHub main
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/golden-palace-update
EOF

cat > /etc/systemd/system/golden-palace-update.timer <<'EOF'
[Unit]
Description=Check Golden Palace GitHub updates every minute

[Timer]
OnBootSec=90
OnUnitActiveSec=60
Unit=golden-palace-update.service

[Install]
WantedBy=timers.target
EOF

PUBLIC_IP="$(curl -4 -fsS --max-time 10 https://api.ipify.org)"
if [ -z "$PUBLIC_IP" ]; then
  echo "Could not determine the VM public IP."
  exit 1
fi
HOST="${PUBLIC_IP//./-}.sslip.io"

cat > /etc/nginx/sites-available/golden-palace <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $HOST;

    location = /manifest.webmanifest {
        alias $APP_DIR/templates/manifest.webmanifest;
        add_header Cache-Control "no-cache";
    }
    location = /sw.js {
        alias $APP_DIR/templates/sw.js;
        add_header Cache-Control "no-cache";
    }
    location = /gp-icon.svg {
        alias $APP_DIR/templates/gp-icon.svg;
        add_header Cache-Control "public, max-age=86400";
    }

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 130s;
        proxy_buffering off;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/golden-palace /etc/nginx/sites-enabled/golden-palace
nginx -t

systemctl daemon-reload
systemctl enable --now golden-palace.service
systemctl enable --now golden-palace-update.timer
systemctl restart nginx

# HTTPS is required for browser camera/getUserMedia. sslip.io gives us a free
# hostname mapped to the VM public IP, so no paid domain is required.
certbot --nginx --non-interactive --agree-tos --register-unsafely-without-email \
  --redirect -d "$HOST" || {
    echo "HTTPS certificate was not issued yet. Make sure Oracle ingress allows TCP 80 and 443, then rerun:"
    echo "  sudo certbot --nginx --redirect -d $HOST"
  }

ufw allow OpenSSH >/dev/null 2>&1 || true
ufw allow 'Nginx Full' >/dev/null 2>&1 || true

cat <<EOF

Golden Palace Oracle host prepared.
TV:       https://$HOST/
Announce: https://$HOST/announce
Health:   https://$HOST/api/health

IMPORTANT: Oracle VCN/security-list ingress must allow TCP 80 and 443.
IMPORTANT: Put Google write credentials in $ENV_FILE before testing manual collection close.
EOF
