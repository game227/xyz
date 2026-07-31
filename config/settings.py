"""
Django settings for XYZ.

Architecture notes (keep in mind before editing):
- Template-based project (no DRF). Session authentication.
- Apps: accounts, education, exam, progress, subscription, core.
- All secrets come from .env — never hardcode credentials here.
"""

import os
from pathlib import Path

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
    'channels',
    'widget_tweaks',
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

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# =========================================================
# DATABASE — PostgreSQL (default). SQLite faqat USE_SQLITE=True da (masalan PA).
# =========================================================
USE_SQLITE = env_bool('USE_SQLITE', False)

if USE_SQLITE:
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

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
