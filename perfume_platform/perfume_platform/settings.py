from pathlib import Path
from datetime import timedelta
import os
import pymysql
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-development-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes', 'on')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if h.strip()]

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.inlines',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'accounts',
    'catalog',
    'cart',
    'orders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'perfume_platform.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [PROJECT_ROOT / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'perfume_platform.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', os.getenv('MYSQL_DATABASE', 'perfume_platform')),
        'USER': os.getenv('DB_USER', os.getenv('MYSQL_USER', 'root')),
        'PASSWORD': os.getenv('DB_PASSWORD', os.getenv('MYSQL_PASSWORD', '')),
        'HOST': os.getenv('DB_HOST', os.getenv('MYSQL_HOST', 'localhost')),
        'PORT': os.getenv('DB_PORT', os.getenv('MYSQL_PORT', '3306')),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_ROOT / 'staticfiles'
STATICFILES_DIRS = [PROJECT_ROOT / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = PROJECT_ROOT / 'media'

CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'True').lower() in ('1', 'true', 'yes', 'on')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'accounts.authentication.CustomJWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "The Last Note Admin",
    "SITE_HEADER": "The Last Note",
    "SITE_SUBHEADER": "Premium Fragrance House",
    "SITE_SYMBOL": "spa",
    "SITE_URL": "/",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "DASHBOARD_CALLBACK": "perfume_platform.dashboard.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "250 250 245", "100": "247 243 233", "200": "238 228 200",
            "300": "226 209 158", "400": "212 185 103", "500": "197 165 74",
            "600": "168 134 25", "700": "134 106 20", "800": "94 74 16",
            "900": "56 44 12", "950": "31 25 8",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Overview"),
                "items": [
                    {"title": _("Dashboard"), "icon": "dashboard",
                     "link": reverse_lazy("admin:index")},
                ],
            },
            {
                "title": _("Commerce"),
                "collapsible": True,
                "items": [
                    {"title": _("Brands"), "icon": "sell",
                     "link": reverse_lazy("admin:accounts_brand_changelist")},
                    {"title": _("Perfumes"), "icon": "spa",
                     "link": reverse_lazy("admin:accounts_perfume_changelist")},
                    {"title": _("Products"), "icon": "inventory_2",
                     "link": reverse_lazy("admin:accounts_product_changelist")},
                    {"title": _("Orders"), "icon": "shopping_bag",
                     "link": reverse_lazy("admin:accounts_customerorder_changelist")},
                    {"title": _("Payments"), "icon": "payments",
                     "link": reverse_lazy("admin:accounts_payment_changelist")},
                    {"title": _("Reviews"), "icon": "rate_review",
                     "link": reverse_lazy("admin:accounts_review_changelist")},
                ],
            },
            {
                "title": _("Operations"),
                "collapsible": True,
                "items": [
                    {"title": _("Users"), "icon": "group",
                     "link": reverse_lazy("admin:accounts_user_changelist")},
                    {"title": _("Roles"), "icon": "badge",
                     "link": reverse_lazy("admin:accounts_role_changelist")},
                    {"title": _("Addresses"), "icon": "location_on",
                     "link": reverse_lazy("admin:accounts_address_changelist")},
                    {"title": _("Cart"), "icon": "shopping_cart",
                     "link": reverse_lazy("admin:accounts_cart_changelist")},
                    {"title": _("Cart Items"), "icon": "shopping_basket",
                     "link": reverse_lazy("admin:accounts_cartitem_changelist")},
                    {"title": _("Order Items"), "icon": "list_alt",
                     "link": reverse_lazy("admin:accounts_orderitem_changelist")},
                    {"title": _("Invoices"), "icon": "receipt_long",
                     "link": reverse_lazy("admin:accounts_invoice_changelist")},
                    {"title": _("Bulk Bottles"), "icon": "local_drink",
                     "link": reverse_lazy("admin:accounts_bulkbottle_changelist")},
                    {"title": _("Decant Batches"), "icon": "inventory",
                     "link": reverse_lazy("admin:accounts_decantbatch_changelist")},
                    {"title": _("FAQs"), "icon": "help",
                     "link": reverse_lazy("admin:accounts_faq_changelist")},
                    {"title": _("Audit Log"), "icon": "history",
                     "link": reverse_lazy("admin:accounts_auditlog_changelist")},
                    {"title": _("Login Attempts"), "icon": "login",
                     "link": reverse_lazy("admin:accounts_loginattempt_changelist")},
                    {"title": _("Chatbot Logs"), "icon": "smart_toy",
                     "link": reverse_lazy("admin:accounts_chatbotlog_changelist")},
                    {"title": _("Password Reset Tokens"), "icon": "key",
                     "link": reverse_lazy("admin:accounts_passwordresettoken_changelist")},
                    {"title": _("Shipping Snapshots"), "icon": "local_shipping",
                     "link": reverse_lazy("admin:orders_ordershippingsnapshot_changelist")},
                    {"title": _("Financial Snapshots"), "icon": "account_balance",
                     "link": reverse_lazy("admin:orders_orderfinancialsnapshot_changelist")},
                    {"title": _("Item Snapshots"), "icon": "content_copy",
                     "link": reverse_lazy("admin:orders_orderitemsnapshot_changelist")},
                    {"title": _("Order Status History"), "icon": "timeline",
                     "link": reverse_lazy("admin:orders_orderstatushistory_changelist")},
                    {"title": _("Return Requests"), "icon": "assignment_return",
                     "link": reverse_lazy("admin:orders_returnrequest_changelist")},
                ],
            },
        ],
    },
}
