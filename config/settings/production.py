from .base import *
from decouple import config

DEBUG = False
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS").split(",")

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
