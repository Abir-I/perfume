from pathlib import Path
from datetime import timedelta
import os
import pymysql
import dj_database_url

# Configure PyMySQL as the MySQL driver for Django
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-88szh(@55*v7ritsi4=+1k%tns0cj)wc66qt0-i(ouzlrj)3nv"
)

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',

    'accounts',
    'catalog',
    'cart',
    'orders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'perfume_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'perfume_platform.wsgi.application'

# ==========================
# Database Configuration
# ==========================

if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"),
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "perfume_platform",
            "USER": "root",
            "PASSWORD": "",
            "HOST": "localhost",
            "PORT": "3306",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# ==========================
# Static Files
# ==========================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR.parent / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==========================
# Media Files
# ==========================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent / 'media'

# ==========================
# CORS
# ==========================

CORS_ALLOW_ALL_ORIGINS = True

# ==========================
# Django REST Framework
# ==========================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'