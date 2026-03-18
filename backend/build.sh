#!/usr/bin/env bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Making migrations..."
python manage.py makemigrations users
python manage.py makemigrations tracker
python manage.py makemigrations

echo "Running migrations..."
python manage.py migrate --no-input

echo "Creating admin user..."
python manage.py shell -c "
import os
from apps.users.models import User
email = os.environ.get('ADMIN_EMAIL', 'admin@admin.com')
password = os.environ.get('ADMIN_PASSWORD', 'admin1234')
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email, password)
    print(f'Admin created: {email}')
else:
    print('Admin already exists')
"

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Build complete!"
