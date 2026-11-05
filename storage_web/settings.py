import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-pr5-development-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "homepage.apps.HomepageConfig",
    "library.apps.LibraryConfig",
    "permissions.apps.PermissionsConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "storage_web.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "homepage.context_processors.site_context",
        ]},
    },
]
STATIC_URL = "/static/"
WSGI_APPLICATION = "storage_web.wsgi.application"
ASGI_APPLICATION = "storage_web.asgi.application"
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CATALOG_PATH = Path(os.environ.get(
    "STORAGE_CATALOG", str(BASE_DIR / "data" / "catalog.json"),
))
EXAMPLE_PATH = BASE_DIR / "data" / "example.json"

STORAGE_DATABASE = Path(os.environ.get(
    "STORAGE_DATABASE", str(BASE_DIR / "data/storage.sqlite"),
))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get(
            "DJANGO_DATABASE", str(BASE_DIR / "db.sqlite3"),
        ),
    },
}

INTERNAL_IPS = ["127.0.0.1", "::1"]
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation." + name}
    for name in (
        "MinimumLengthValidator", "CommonPasswordValidator",
        "NumericPasswordValidator",
    )
]
