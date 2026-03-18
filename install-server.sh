#!/bin/bash
# ============================================================
#   UniTrack — Oracle Cloud / Ubuntu Server Installer
#   Run with: sudo bash install-server.sh
# ============================================================
set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${CYAN}[•] $1${NC}"; }
success() { echo -e "${GREEN}[✓] $1${NC}"; }
error()   { echo -e "${RED}[✗] $1${NC}"; exit 1; }

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗"
echo -e "║   UniTrack — Oracle Cloud Installer       ║"
echo -e "╚══════════════════════════════════════════╝${NC}"
echo ""

[ "$EUID" -ne 0 ] && error "Run as root: sudo bash install-server.sh"

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$INSTALL_DIR/backend"
FRONTEND_DIR="$INSTALL_DIR/frontend"
ANGULAR_BUILD="$FRONTEND_DIR/dist/unitracker-frontend/browser"
DIST_DIR="$BACKEND_DIR/frontend_dist/browser"

# Detect real user
REAL_USER="${SUDO_USER:-ubuntu}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

info "Installing for user: $REAL_USER"
info "Server IP: $SERVER_IP"

# ── STEP 1: System packages ────────────────────────────────
info "Step 1/7 — Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    nodejs npm curl unzip git \
    nginx ufw
success "System packages installed"

# ── STEP 2: Node / Angular ─────────────────────────────────
info "Step 2/7 — Installing Angular CLI..."
npm install -g @angular/cli --silent 2>/dev/null || true
success "Angular CLI ready"

# ── STEP 3: Python environment ─────────────────────────────
info "Step 3/7 — Setting up Python environment..."
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -r requirements.txt
pip install --quiet gunicorn  # for production serving
success "Python packages installed"

# ── STEP 4: Database ───────────────────────────────────────
info "Step 4/7 — Setting up database..."
python manage.py makemigrations users --no-input 2>/dev/null || true
python manage.py makemigrations tracker --no-input 2>/dev/null || true
python manage.py migrate --no-input
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(email='admin@admin.com').exists():
    User.objects.create_superuser('admin@admin.com', 'admin1234')
    print('Admin created.')
else:
    print('Admin already exists.')
"
# Fix ownership so service can write to db
chown -R "$REAL_USER:$REAL_USER" "$BACKEND_DIR"
chmod 664 "$BACKEND_DIR/db.sqlite3"
success "Database ready"

# ── STEP 5: Build Angular ──────────────────────────────────
info "Step 5/7 — Building Angular frontend..."
cd "$FRONTEND_DIR"
rm -rf node_modules package-lock.json 2>/dev/null || true
npm install --legacy-peer-deps --silent
npx ng build --configuration production

# Copy to backend
mkdir -p "$DIST_DIR"
if [ -d "$ANGULAR_BUILD" ]; then
    cp -r "$ANGULAR_BUILD"/. "$DIST_DIR/"
else
    cp -r "$FRONTEND_DIR/dist/unitracker-frontend"/. "$DIST_DIR/"
fi

cd "$BACKEND_DIR"
source venv/bin/activate
python manage.py collectstatic --no-input -v 0 2>/dev/null || true
chown -R "$REAL_USER:$REAL_USER" "$BACKEND_DIR"
success "Frontend built and deployed"

# ── STEP 6: Systemd service ────────────────────────────────
info "Step 6/7 — Creating systemd service..."
cat > /etc/systemd/system/unitracker.service << EOF
[Unit]
Description=UniTrack University Progress Tracker
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$BACKEND_DIR
ExecStart=$BACKEND_DIR/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 120
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:/var/log/unitracker.log
StandardError=append:/var/log/unitracker.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable unitracker.service
systemctl restart unitracker.service
success "UniTrack service started"

# ── STEP 7: Nginx reverse proxy ────────────────────────────
info "Step 7/7 — Configuring Nginx..."
cat > /etc/nginx/sites-available/unitracker << EOF
server {
    listen 80;
    server_name $SERVER_IP _;

    # Serve Angular static files directly (faster)
    location /assets/ {
        alias $DIST_DIR/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Everything else → Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        client_max_body_size 10M;
    }
}
EOF

# Enable site
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/unitracker /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx && systemctl enable nginx
success "Nginx configured"

# ── Firewall ───────────────────────────────────────────────
ufw allow ssh
ufw allow 80
ufw allow 8000
ufw --force enable
success "Firewall configured"

# ── DONE ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗"
echo -e "║        UniTrack Deployed Successfully!       ║"
echo -e "╠══════════════════════════════════════════════╣"
echo -e "║                                              ║"
echo -e "║  🌐 App:    http://$SERVER_IP              ║"
echo -e "║  🌐 App:    http://$SERVER_IP:8000         ║"
echo -e "║  🛡️  Admin:  http://$SERVER_IP/admin       ║"
echo -e "║                                              ║"
echo -e "║  Login:  admin@admin.com / admin1234         ║"
echo -e "║                                              ║"
echo -e "║  Auto-starts on boot ✓                       ║"
echo -e "╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Logs: tail -f /var/log/unitracker.log${NC}"
echo -e "${CYAN}Restart: sudo systemctl restart unitracker${NC}"
