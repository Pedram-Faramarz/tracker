#!/bin/bash
set -e

echo "============================================"
echo "  UniTrack - Auto Setup Script (Mac/Linux)"
echo "============================================"
echo ""

# ── BACKEND SETUP ────────────────────────────────────────────────────────────
echo "[1/6] Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

echo "[2/6] Installing Python dependencies..."
pip install -r requirements.txt

echo "[3/6] Running database migrations..."
python manage.py makemigrations users
python manage.py makemigrations tracker
python manage.py migrate

echo "[4/6] Creating superuser (admin@admin.com / admin1234)..."
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(email='admin@admin.com').exists():
    User.objects.create_superuser('admin@admin.com', 'admin1234')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"

echo "[5/6] Starting Django backend on port 8000..."
# Start backend in background
source venv/bin/activate && python manage.py runserver &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# ── FRONTEND SETUP ───────────────────────────────────────────────────────────
cd ../frontend

echo "[6/6] Installing Angular dependencies..."
npm install

echo "Starting Angular frontend on port 4200..."
npm start &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "============================================"
echo "  SUCCESS! UniTrack is running:"
echo ""
echo "  Frontend  →  http://localhost:4200"
echo "  Backend   →  http://localhost:8000"
echo "  Admin     →  http://localhost:8000/admin"
echo ""
echo "  Admin login:  admin@admin.com / admin1234"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all servers."

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
