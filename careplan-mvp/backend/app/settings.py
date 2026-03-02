import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "mvp-secret-key-change-in-prod"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "app",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = "app.urls"

DATABASES = {}  # No database

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Anthropic API key from environment
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
