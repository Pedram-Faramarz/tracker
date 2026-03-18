@echo off
echo ============================================
echo   UniTrack - Auto Setup Script (Windows)
echo ============================================
echo.

:: ── BACKEND SETUP ───────────────────────────────────────────────────────────
echo [1/6] Setting up Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat

echo [2/6] Installing Python dependencies...
pip install -r requirements.txt

echo [3/6] Running database migrations...
python manage.py makemigrations users
python manage.py makemigrations tracker
python manage.py migrate

echo [4/6] Creating admin account (admin@admin.com / admin1234)...
python manage.py shell -c "from apps.users.models import User; User.objects.filter(email='admin@admin.com').exists() or User.objects.create_superuser('admin@admin.com', 'admin1234')"

echo [5/6] Starting Django backend...
start "UniTrack Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python manage.py runserver"

:: ── FRONTEND SETUP ──────────────────────────────────────────────────────────
cd ..\frontend

echo [6/6] Clean installing Angular dependencies (this may take a few minutes)...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json
call npm install

echo Starting Angular frontend...
start "UniTrack Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo ============================================
echo   SUCCESS! UniTrack is running:
echo.
echo   Frontend  ->  http://localhost:4200
echo   Backend   ->  http://localhost:8000
echo   Admin     ->  http://localhost:8000/admin
echo.
echo   Admin login:  admin@admin.com / admin1234
echo ============================================
echo.
pause
