#!/bin/bash
# ============================================================
#   UniTrack — Kali Linux Installer
#   Run once with:  sudo bash install-kali.sh
# ============================================================

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

info()    { echo -e "${CYAN}[•] $1${NC}"; }
success() { echo -e "${GREEN}[✓] $1${NC}"; }
error()   { echo -e "${RED}[✗] $1${NC}"; exit 1; }

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗"
echo -e "║     UniTrack — Kali Installer         ║"
echo -e "╚══════════════════════════════════════╝${NC}"
echo ""

[ "$EUID" -ne 0 ] && error "Please run as root: sudo bash install-kali.sh"

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$INSTALL_DIR/backend"
FRONTEND_DIR="$INSTALL_DIR/frontend"
# Angular 17 outputs to dist/unitracker-frontend/browser/
ANGULAR_BUILD="$FRONTEND_DIR/dist/unitracker-frontend/browser"
# Django expects it here
DIST_DIR="$BACKEND_DIR/frontend_dist/browser"

REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo $USER)}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
info "Installing for user: $REAL_USER"

# ── STEP 1: System packages ────────────────────────────────
info "Step 1/6 — Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nodejs npm
success "System packages ready"

# ── STEP 2: Python virtual environment ────────────────────
info "Step 2/6 — Setting up Python environment..."
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -r requirements.txt
success "Python packages installed"

# ── STEP 3: Database ───────────────────────────────────────
info "Step 3/6 — Setting up database..."
python manage.py makemigrations users --no-input 2>/dev/null || true
python manage.py makemigrations tracker --no-input 2>/dev/null || true
python manage.py migrate --no-input
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(email='admin@admin.com').exists():
    User.objects.create_superuser('admin@admin.com', 'admin1234')
    print('Admin created: admin@admin.com / admin1234')
else:
    print('Admin already exists')
"
# FIX: ensure db and backend folder are owned by real user, not root
 chown -R "$REAL_USER:$REAL_USER" "$BACKEND_DIR"
 chmod 664 "$BACKEND_DIR/db.sqlite3" 2>/dev/null || true
 success "Database ready (owned by $REAL_USER)"

# ── STEP 4: Build Angular ──────────────────────────────────
info "Step 4/6 — Building Angular frontend..."
cd "$FRONTEND_DIR"
rm -rf node_modules package-lock.json 2>/dev/null || true
npm install --legacy-peer-deps --silent
npx ng build --configuration production

# Copy Angular build into backend folder
mkdir -p "$DIST_DIR"
cp -r "$ANGULAR_BUILD"/. "$DIST_DIR/"
success "Angular built and copied to backend/frontend_dist/browser/"

# Verify index.html exists
if [ ! -f "$DIST_DIR/index.html" ]; then
    # fallback: maybe no browser/ subdir
    ANGULAR_BUILD_ALT="$FRONTEND_DIR/dist/unitracker-frontend"
    if [ -f "$ANGULAR_BUILD_ALT/index.html" ]; then
        mkdir -p "$BACKEND_DIR/frontend_dist/browser"
        cp -r "$ANGULAR_BUILD_ALT"/. "$BACKEND_DIR/frontend_dist/browser/"
        success "Copied from fallback path"
    else
        echo -e "${RED}Could not find Angular build output. Check npm build logs.${NC}"
        exit 1
    fi
fi

# ── STEP 5: Collect Django static files ───────────────────
cd "$BACKEND_DIR"
source venv/bin/activate
python manage.py collectstatic --no-input --clear -v 0 2>/dev/null || true

# ── STEP 6: Systemd service ────────────────────────────────
info "Step 5/6 — Creating systemd autostart service..."
cat > /etc/systemd/system/unitracker.service << SVCEOF
[Unit]
Description=UniTrack University Progress Tracker
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$BACKEND_DIR
ExecStart=$BACKEND_DIR/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:/var/log/unitracker.log
StandardError=append:/var/log/unitracker.log

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable unitracker.service
systemctl restart unitracker.service
success "Service enabled and started"

# ── Auto-open browser ──────────────────────────────────────
info "Step 6/6 — Setting up browser auto-open..."
AUTOSTART_DIR="$REAL_HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
chown "$REAL_USER:$REAL_USER" "$AUTOSTART_DIR" 2>/dev/null || true

cat > "$AUTOSTART_DIR/unitracker.desktop" << DESKEOF
[Desktop Entry]
Type=Application
Name=UniTrack
Exec=bash -c "sleep 4 && xdg-open http://localhost:8000"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
DESKEOF

chown "$REAL_USER:$REAL_USER" "$AUTOSTART_DIR/unitracker.desktop"
success "Browser auto-open configured"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗"
echo -e "║       Installation Complete! ✓            ║"
echo -e "╠═══════════════════════════════════════════╣"
echo -e "║  App:    http://localhost:8000             ║"
echo -e "║  Admin:  http://localhost:8000/admin       ║"
echo -e "║  Login:  admin@admin.com / admin1234       ║"
echo -e "║                                            ║"
echo -e "║  Auto-starts on every boot ✓               ║"
echo -e "║  Works 100% offline ✓                      ║"
echo -e "╚═══════════════════════════════════════════╝${NC}"
echo ""
sudo -u "$REAL_USER" xdg-open http://localhost:8000 2>/dev/null || \
    echo -e "${YELLOW}Open browser manually: http://localhost:8000${NC}"
