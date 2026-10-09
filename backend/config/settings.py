"""
Ajustes de Django/Wagtail para el backend del portfolio.

Todo lo sensible o dependiente del entorno se lee de variables de entorno
(ver README.md). Sin variables, funciona en local con SQLite y disco.
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --- Básicos ---------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = env_bool("DEBUG", False)

# URL pública del backend (admin + medios). En Railway se deduce del dominio.
_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
PUBLIC_BASE_URL = (
    os.environ.get("PUBLIC_BASE_URL")
    or (f"https://{_railway_domain}" if _railway_domain else "http://localhost:8000")
).rstrip("/")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "*")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS") + [PUBLIC_BASE_URL]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
if not DEBUG:
    SESSION_COOKIE_SECURE = PUBLIC_BASE_URL.startswith("https://")
    CSRF_COOKIE_SECURE = PUBLIC_BASE_URL.startswith("https://")

# --- Apps ------------------------------------------------------------------
INSTALLED_APPS = [
    "portfolio",
    "wagtail.contrib.settings",
    "wagtail.snippets",
    "wagtail.images",
    "wagtail.documents",  # el admin de Wagtail referencia su API; el menú se oculta (solo se usan imágenes)
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "wagtail.users",
    "wagtail.sites",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Base de datos (Postgres en Railway vía DATABASE_URL) -------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# El buscador de Wagtail sobre Postgres usa SearchVectorField / GinIndex.
if "postgresql" in DATABASES["default"]["ENGINE"]:
    INSTALLED_APPS.append("django.contrib.postgres")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Idioma / zona horaria --------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos y medios -------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Los medios siempre se sirven por la vista proxy `/media/...` (ver portfolio.views),
# porque los buckets de Railway son privados.
MEDIA_URL = f"{PUBLIC_BASE_URL}/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

AWS_BUCKET = os.environ.get("AWS_S3_BUCKET_NAME")
if AWS_BUCKET:
    STORAGES["default"] = {
        "BACKEND": "portfolio.storage.BucketStorage",
        "OPTIONS": {
            "bucket_name": AWS_BUCKET,
            "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL"),
            "access_key": os.environ.get("AWS_ACCESS_KEY_ID"),
            "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
            "region_name": os.environ.get("AWS_S3_REGION_NAME") or "auto",
            "signature_version": "s3v4",
            "addressing_style": os.environ.get("AWS_S3_ADDRESSING_STYLE", "virtual"),
            "default_acl": None,
            "querystring_auth": False,
            "file_overwrite": False,
            "object_parameters": {"CacheControl": "public, max-age=31536000, immutable"},
        },
    }

# --- Wagtail -----------------------------------------------------------------
WAGTAIL_SITE_NAME = "Portfolio · Admin"
WAGTAILADMIN_BASE_URL = PUBLIC_BASE_URL
WAGTAIL_ENABLE_UPDATE_CHECK = False
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 30 * 1024 * 1024
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "avif"]
WAGTAILSEARCH_BACKENDS = {"default": {"BACKEND": "wagtail.search.backends.database"}}
WAGTAILADMIN_PERMITTED_LANGUAGES = [("es", "Español"), ("en", "English")]
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000

# --- Logging -----------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
