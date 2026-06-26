import os
import subprocess
import sys


def dev():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    subprocess.run(
        [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'],
        check=True,
    )


def start():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    subprocess.run(
        ['gunicorn', 'config.wsgi:application', '--bind', '0.0.0.0:8000', '--workers', '3'],
        check=True,
    )
