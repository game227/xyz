"""
Django settings for XYZ.

Architecture notes (keep in mind before editing):
- Template-based project (no DRF). Session authentication.
- Apps: accounts, education, exam, progress, subscription, core.
- All secrets come from .env — never hardcode credentials here.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


# =========================================================
# CORE
# =========================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'insecure-dev-key-change-me')
DEBUG = env_bool('DEBUG', True)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

# Render / boshqa PaaS hostlar
_render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME', '').strip()
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
if _render_host:
    _origin = f'https://{_render_host}'
    if _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)

# HTTPS ortida (Render / Railway / Runsite)
if env_bool('BEHIND_PROXY', bool(_render_host)):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = not DEBUG
    CSRF_COOKIE_SECURE = not DEBUG


# =========================================================
# APPLICATIONS
# =========================================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'widget_tweaks',
    'storages',
]

LOCAL_APPS = [
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.education.apps.EducationConfig',
    'apps.exam.apps.ExamConfig',
    'apps.progress.apps.ProgressConfig',
    'apps.subscription.apps.SubscriptionConfig',
    'apps.teacher.apps.TeacherConfig',
    'apps.live.apps.LiveConfig',
]

INSTALLED_APPS = ['daphne'] + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.subscription.middleware.SubscriptionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_branding',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# =========================================================
# DATABASE — DATABASE_URL (Render/Neon) > SQLite > PostgreSQL env
# =========================================================
USE_SQLITE = env_bool('USE_SQLITE', False)
_database_url = os.getenv('DATABASE_URL', '').strip()

if _database_url:
    DATABASES = {
        'default': dj_database_url.parse(
            _database_url,
            conn_max_age=60,
            ssl_require=env_bool('DB_SSL_REQUIRE', True),
        )
    }
elif USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'xyz'),
            'USER': os.getenv('DB_USER', 'xyz_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }

# =========================================================
# PASSWORD VALIDATION
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    # Faqat uzunlik: kamida 8 belgi. Qolgan qat’iy talablar olib tashlangan.
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
]

# =========================================================
# INTERNATIONALIZATION
# =========================================================
LANGUAGE_CODE = 'uz'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Tashkent')
USE_I18N = True
USE_TZ = True

# =========================================================
# STATIC & MEDIA
# =========================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------
# Media uchun S3-mos ombor (ixtiyoriy).
#
# MUHIM: Render (va ko'p PaaS)dagi bepul veb-xizmatlar diskni "vaqtinchalik"
# saqlaydi — har safar qayta deploy qilinganda (masalan avtomatik GitHub
# deploy ishga tushganda) serverdagi disk TOZALANADI va shu paytgacha
# foydalanuvchilar yuklagan barcha rasm/video/logo YO'QOLADI, chunki ular
# oddiy diskka (MEDIA_ROOT) saqlanadi.
#
# Buning oldini olish uchun: AWS S3 yoki S3-mos ombor (Cloudflare R2,
# Backblaze B2 va h.k.)ni sozlab, quyidagi environment o'zgaruvchilarini
# beriladi — shunda media fayllar diskdan emas, tashqi, doimiy ombordan
# xizmat qiladi va har deployda saqlanib qoladi:
#   AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
#   AWS_S3_REGION_NAME (masalan "auto" yoki "eu-central-1"),
#   AWS_S3_ENDPOINT_URL (S3 bo'lmagan xizmatlar uchun, masalan R2 uchun kerak)
# Hech biri berilmasa — hammasi avvalgidek, oddiy diskka saqlanadi (dev uchun bemalol).
# ---------------------------------------------------------------
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '').strip()
if AWS_STORAGE_BUCKET_NAME:
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'auto')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', '').strip() or None
    AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', '').strip() or None
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================================================
# AUTHENTICATION (Phase 2)
# =========================================================
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'progress:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

# Parol tiklash (dev: konsolga chiqaradi; prod da SMTP sozlang)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'XYZ <noreply@xyz.uz>')

# =========================================================
# LOGGING (see apps/core — expanded in later phases)
# =========================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
