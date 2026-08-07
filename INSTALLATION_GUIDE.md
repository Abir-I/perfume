# 🚀 Installation Guide - The Last Note Premium Admin Dashboard v4.0

## System Requirements

- Python 3.8+
- Django 5.0+
- Django REST Framework
- MySQL 5.7+ or MariaDB
- Node.js (optional, for minification)
- Modern web browser (Chrome, Firefox, Safari, Edge)

---

## Step 1: Clone/Download Project

```bash
cd your-project-directory
# Place the perfume_build folder content into your project
```

---

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Database Configuration

### **Update Django Settings**

Edit `perfume_platform/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    'accounts',
    'catalog',
    'cart',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'accounts.authentication.CustomJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

---

## Step 4: Run Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Load initial data (if available)
python manage.py loaddata initial_data.json
```

---

## Step 5: Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin user
```

---

## Step 6: Copy Static Files

```bash
# Collect all static files
python manage.py collectstatic --noinput

# Or for development with auto-reload:
python manage.py collectstatic
```

---

## Step 7: Update URL Configuration

Edit `perfume_platform/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/catalog/', include('catalog.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    
    # Admin Premium Dashboard
    path('admin/dashboard/', TemplateView.as_view(template_name='admin_premium.html'), name='admin-dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

---

## Step 8: Start Development Server

```bash
python manage.py runserver
```

---

## Step 9: Access the Admin Dashboard

1. **Login First** - Go to `http://localhost:8000/login`
2. **Access Dashboard** - Go to `http://localhost:8000/admin/dashboard/`

---

## Troubleshooting Installation

### **Issue: ModuleNotFoundError**

**Solution:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### **Issue: Database Connection Error**

**Solution:**
1. Verify MySQL is running
2. Check database credentials in `settings.py`
3. Ensure database exists:
```sql
CREATE DATABASE perfume_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### **Issue: Static Files Not Loading**

**Solution:**
```bash
python manage.py collectstatic --clear --noinput
```

### **Issue: Template Not Found**

**Solution:**
- Verify `TEMPLATES` configuration in `settings.py`
- Ensure templates folder path is correct
- Check file names match exactly (case-sensitive on Linux)

### **Issue: CORS Error**

**Solution:**
Add your domain to `CORS_ALLOWED_ORIGINS` in `settings.py`

---

## Production Setup

### **1. Update Settings for Production**

```python
# settings.py
DEBUG = False

ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],
    'style-src': ["'self'", "'unsafe-inline'"],
}
```

### **2. Use Production Database**

- Migrate to PostgreSQL or production MySQL
- Update `DATABASES` settings
- Use environment variables for credentials

### **3. Set Up Web Server**

**Option A: Gunicorn**
```bash
pip install gunicorn
gunicorn perfume_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Option B: uWSGI**
```bash
pip install uwsgi
uwsgi --http :8000 --wsgi-file perfume_platform/wsgi.py --master --processes 4 --threads 2
```

### **4. Configure Nginx**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **5. Set Up SSL/TLS**

```bash
# Using Let's Encrypt with Certbot
sudo certbot certonly --nginx -d yourdomain.com
```

### **6. Enable Compression**

```python
# settings.py
MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')
```

---

## Monitoring & Logging

### **Set Up Logging**

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### **Monitor Performance**

```bash
pip install django-debug-toolbar
pip install django-extensions
```

---

## Backup & Recovery

### **Database Backup**

```bash
# MySQL dump
mysqldump -u root -p perfume_db > backup.sql

# Restore
mysql -u root -p perfume_db < backup.sql
```

### **Static Files Backup**

```bash
tar -czf static_backup.tar.gz static/
tar -czf media_backup.tar.gz media/
```

---

## Performance Optimization

### **Enable Caching**

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### **Optimize Database Queries**

```python
# Use select_related and prefetch_related
from django.db.models import Prefetch

products = Product.objects.select_related('perfume', 'perfume__brand').prefetch_related('cartitem_set')
```

---

## Testing

### **Run Tests**

```bash
python manage.py test

# Run specific app tests
python manage.py test catalog

# Run specific test case
python manage.py test catalog.tests.AdminViewsTest
```

### **Load Test**

```bash
pip install locust

# Create locustfile.py and run:
locust -f locustfile.py -u 100 -r 10 -t 5m
```

---

## Upgrade Guide

### **From v3.0 to v4.0**

1. Backup database and static files
2. Update all CSS files (new animations included)
3. Update all JS files (new dashboard included)
4. Update URL configuration
5. Run migrations
6. Test admin dashboard
7. Deploy to production

---

## Support Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
- **Browser Compatibility**: https://caniuse.com/

---

## Next Steps

1. ✅ Complete installation
2. ✅ Test admin dashboard
3. ✅ Customize branding & colors
4. ✅ Set up user roles & permissions
5. ✅ Deploy to production
6. ✅ Monitor performance
7. ✅ Gather user feedback

---

**Installation Complete! 🎉**

Your admin dashboard is now ready to use. Visit `http://localhost:8000/admin/dashboard/` to get started.
