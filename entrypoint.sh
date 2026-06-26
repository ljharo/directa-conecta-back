#!/bin/sh
set -e

echo ">>> Aplicando migraciones..."
python manage.py makemigrations centros usuarios personas --no-input
python manage.py migrate --no-input

echo ">>> Creando superusuario (si no existe)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ['DJANGO_SUPERUSER_USERNAME']
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=os.environ.get('DJANGO_SUPERUSER_EMAIL', ''),
        password=os.environ['DJANGO_SUPERUSER_PASSWORD'],
    )
    print(f'Superusuario \"{username}\" creado.')
else:
    print(f'Superusuario \"{username}\" ya existe, se omite.')
"

exec "$@"
