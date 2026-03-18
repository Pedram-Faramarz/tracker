#!/bin/bash
# ============================================================
#   UniTrack — PythonAnywhere Installer
#   Run this in PythonAnywhere Bash console:
#   bash install-pythonanywhere.sh YOURNAME
# ============================================================

set -e
GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

info()    { echo -e "${CYAN}[•] $1${NC}"; }
success() { echo -e "${GREEN}[✓] $1${NC}"; }
error()   { echo -e "${RED}[✗] $1${NC}"; exit 1; }

USERNAME="${1:-}"
[ -z "$USERNAME" ] && error "Usage: bash install-pythonanywhere.sh YOURNAME"

INSTALL_DIR="/home/$USERNAME/unitracker"
BACKEND_DIR="$INSTALL_DIR/backend"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗"
echo -e "║  UniTrack — PythonAnywhere Installer      ║"
echo -e "╚══════════════════════════════════════════╝${NC}"
echo ""

# ── STEP 1: Fix username in config files ──────────────────
info "Step 1/5 — Configuring for user: $USERNAME..."
sed -i "s/YOURNAME/$USERNAME/g" "$BACKEND_DIR/config/settings_pythonanywhere.py"
sed -i "s/YOURNAME/$USERNAME/g" "$BACKEND_DIR/config/wsgi_pythonanywhere.py"
success "Username configured"

# ── STEP 2: Python virtual environment ────────────────────
info "Step 2/5 — Setting up Python environment..."
cd "$BACKEND_DIR"
python3.11 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -r requirements.txt
success "Python packages installed"

# ── STEP 3: Database ───────────────────────────────────────
info "Step 3/5 — Setting up database..."
export DJANGO_SETTINGS_MODULE=config.settings_pythonanywhere
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
success "Database ready"

# ── STEP 4: Static files ───────────────────────────────────
info "Step 4/5 — Collecting static files..."
python manage.py collectstatic --no-input -v 0
success "Static files collected"

# ── STEP 5: Build Angular frontend ────────────────────────
info "Step 5/5 — Building Angular frontend..."
cd /home/$USERNAME/unitracker/frontend
npm install --legacy-peer-deps --silent

# Update API URL for PythonAnywhere
cat > src/environments/environment.ts << ENVEOF
export const environment = {
  production: true,
  apiUrl: 'https://$USERNAME.pythonanywhere.com/api',
};
ENVEOF

npm run build -- --configuration production \
  --output-path="/home/$USERNAME/unitracker/frontend_built"
success "Frontend built"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗"
echo -e "║     Installation Complete!                         ║"
echo -e "╠════════════════════════════════════════════════════╣"
echo -e "║                                                    ║"
echo -e "║  Now follow these steps in PythonAnywhere:         ║"
echo -e "║                                                    ║"
echo -e "║  1. Go to Web tab → Add new web app               ║"
echo -e "║  2. Choose Manual Configuration → Python 3.11     ║"
echo -e "║  3. Set WSGI file to:                             ║"
echo -e "║     /home/$USERNAME/unitracker/backend/config/wsgi_pythonanywhere.py  ║"
echo -e "║  4. Set Virtualenv to:                            ║"
echo -e "║     /home/$USERNAME/unitracker/backend/venv       ║"
echo -e "║  5. Add Static Files:                             ║"
echo -e "║     URL: /static/                                 ║"
echo -e "║     Dir: /home/$USERNAME/unitracker/backend/staticfiles  ║"
echo -e "║     URL: /                                        ║"
echo -e "║     Dir: /home/$USERNAME/unitracker/frontend_built ║"
echo -e "║  6. Click Reload                                  ║"
echo -e "║                                                    ║"
echo -e "║  🌐 Your app: https://$USERNAME.pythonanywhere.com ║"
echo -e "║  🛡️  Admin: https://$USERNAME.pythonanywhere.com/admin ║"
echo -e "║  Login: admin@admin.com / admin1234               ║"
echo -e "╚════════════════════════════════════════════════════╝${NC}"
