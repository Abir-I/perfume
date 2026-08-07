# PERFUME E-COMMERCE PLATFORM - COMPLETE SETUP & DEPLOYMENT GUIDE

## 🎯 PROJECT OVERVIEW

This is a **production-grade**, fully functional perfume e-commerce platform built with:
- **Backend:** Django + Django REST Framework
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Database:** PostgreSQL (recommended) / SQLite (development)
- **Features:** Complete shopping, customer dashboard, order tracking, reviews, wishlist

---

## 📋 WHAT'S INCLUDED

### ✅ IMPLEMENTED FEATURES

#### Customer Features
- ✅ **Browse Products** - Full catalog with filtering by brand
- ✅ **Add to Cart** - AJAX-powered with instant feedback and animations
- ✅ **Shopping Cart** - View, update quantities, remove items
- ✅ **Checkout** - Complete order placement with shipping info
- ✅ **Order Tracking** - Real-time status updates and tracking
- ✅ **Customer Dashboard** - Production-quality dashboard with:
  - 📊 Dashboard overview with statistics
  - 👤 Profile management
  - 📦 Order history and details
  - ⭐ Product reviews (add/edit/delete)
  - ❤️ Wishlist
  - 📍 Saved addresses
  - ⚙️ Account settings
  - 📋 Activity log

#### Admin Features
- ✅ **Product Management** - Add, edit, delete products
- ✅ **Order Management** - View and update order status
- ✅ **Customer Management** - View customer data
- ✅ **Analytics** - Sales reports and statistics

---

## 🚀 QUICK START (5 MINUTES)

### Prerequisites
```bash
# Required
- Python 3.8+
- pip & virtualenv
- PostgreSQL 12+ (recommended) OR SQLite

# Optional
- Node.js (for asset building)
- Docker (for containerization)
```

### Installation Steps

```bash
# 1. Extract project
unzip perfume_PREMIUM_COMPLETE_v2.zip
cd perfume_production/perfume_platform

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r ../requirements.txt

# 5. Setup database
python manage.py migrate

# 6. Create admin user
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver

# 8. Open in browser
# http://localhost:8000
```

---

## 🔧 CONFIGURATION

### Environment Setup

Create `.env` file in `perfume_platform/` directory:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-super-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database - SQLite (Development)
DATABASE_URL=sqlite:///db.sqlite3

# OR Database - PostgreSQL (Production Recommended)
DATABASE_URL=postgresql://user:password@localhost:5432/perfume_db

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for production media storage)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Payment Gateway (optional)
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
```

### Django Settings Updates

In `perfume_platform/settings.py`:

```python
# For Production
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'perfume_db',
        'USER': 'perfume_user',
        'PASSWORD': 'strong_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static & Media Files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_URL = '/media/'

# Security Settings
CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 🗄️ DATABASE SETUP

### Option 1: SQLite (Development)

```bash
# Already configured by default
python manage.py migrate

# Load sample data (if available)
python manage.py shell < load_sample_data.py
```

### Option 2: PostgreSQL (Production)

```bash
# 1. Install PostgreSQL
# Windows: Download from https://www.postgresql.org/download/
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql postgresql-contrib

# 2. Create database user and database
sudo -u postgres psql
CREATE USER perfume_user WITH PASSWORD 'strong_password';
CREATE DATABASE perfume_db OWNER perfume_user;
ALTER ROLE perfume_user SET client_encoding TO 'utf8';
ALTER ROLE perfume_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE perfume_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE perfume_db TO perfume_user;
\q

# 3. Update DATABASE_URL in .env
DATABASE_URL=postgresql://perfume_user:strong_password@localhost:5432/perfume_db

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser
```

---

## ▶️ RUNNING THE APPLICATION

### Development

```bash
# Method 1: Simple (single terminal)
python manage.py runserver

# Method 2: With console logging
python manage.py runserver --verbosity 2

# Method 3: Custom port
python manage.py runserver 8001

# Access at http://localhost:8000
```

### Production (Gunicorn)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn perfume_platform.wsgi:application --bind 0.0.0.0:8000

# Or with multiple workers
gunicorn perfume_platform.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120
```

---

## 🌐 DEPLOYMENT OPTIONS

### Option 1: Heroku (Easiest)

```bash
# 1. Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# 2. Login to Heroku
heroku login

# 3. Create Heroku app
heroku create your-perfume-app

# 4. Add Procfile (create in root)
echo "web: gunicorn perfume_platform.wsgi" > Procfile

# 5. Add runtime.txt
echo "python-3.9.16" > runtime.txt

# 6. Configure environment
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ALLOWED_HOSTS=your-perfume-app.herokuapp.com

# 7. Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# 8. Deploy
git push heroku main

# 9. Run migrations
heroku run python manage.py migrate

# 10. Create superuser
heroku run python manage.py createsuperuser

# Access at https://your-perfume-app.herokuapp.com
```

### Option 2: DigitalOcean App Platform

```bash
# 1. Connect GitHub repository
# 2. Create new app in DigitalOcean App Platform
# 3. Select Django as app type
# 4. Configure environment variables in UI
# 5. Deploy

# Or deploy directly:
doctl apps create --spec app.yaml
```

### Option 3: AWS EC2 (Advanced)

```bash
# 1. Launch EC2 instance (Ubuntu 20.04)
# 2. Connect via SSH
ssh -i key.pem ubuntu@your-instance-ip

# 3. Setup server
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv postgresql nginx git

# 4. Clone project
git clone https://github.com/yourusername/perfume-platform.git
cd perfume-platform/perfume_platform

# 5. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt

# 6. Configure environment
nano .env  # Edit .env with production settings

# 7. Run migrations
python manage.py migrate
python manage.py collectstatic --noinput

# 8. Setup Gunicorn systemd service
sudo nano /etc/systemd/system/gunicorn.service
```

Create `/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=Gunicorn daemon for Perfume Platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/perfume-platform/perfume_platform
Environment="PATH=/var/www/perfume-platform/perfume_platform/venv/bin"
ExecStart=/var/www/perfume-platform/perfume_platform/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/var/www/perfume-platform/perfume_platform/gunicorn.sock \
    perfume_platform.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# 9. Setup Nginx
sudo nano /etc/nginx/sites-available/perfume
```

Create `/etc/nginx/sites-available/perfume`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /var/www/perfume-platform/perfume_platform/staticfiles/;
    }

    location /media/ {
        alias /var/www/perfume-platform/perfume_platform/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/perfume-platform/perfume_platform/gunicorn.sock;
    }
}
```

```bash
# 10. Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/perfume /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 11. Enable HTTPS with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 🔑 USING THE PLATFORM

### For Customers

1. **Create Account**
   - Click "Login" in navbar
   - Click "Register" tab
   - Fill form and submit

2. **Browse Products**
   - Click "Shop" to see all products
   - Click "Brands" to browse by brand
   - Click on product to see details

3. **Add to Cart**
   - Click "Add to Cart" button
   - See confirmation notification
   - Cart count updates instantly

4. **View Dashboard**
   - Click profile icon in navbar
   - View orders, reviews, addresses
   - Manage account settings

5. **Place Order**
   - Go to cart
   - Click "Checkout"
   - Enter shipping details
   - Place order

### For Admins

1. **Access Admin Panel**
   - Go to `/admin/`
   - Login with superuser account

2. **Manage Products**
   - Navigate to Catalog
   - Add/Edit/Delete products
   - Upload images

3. **Manage Orders**
   - View all customer orders
   - Update order status
   - Track shipments

4. **View Reports**
   - Check sales analytics
   - View customer statistics

---

## 🐛 TROUBLESHOOTING

### Common Issues & Solutions

#### "ModuleNotFoundError"
```bash
# Solution: Install all dependencies
pip install -r requirements.txt
```

#### "Static files not loading"
```bash
# Solution: Collect static files
python manage.py collectstatic --noinput
```

#### "Database connection error"
```bash
# Check DATABASE_URL in .env
# Verify database server is running
# Test connection: psql -U user -d perfume_db -h localhost
```

#### "403 Forbidden on Add to Cart"
```
# Check CSRF token is present
# Verify X-CSRFToken header in requests
# Clear browser cookies and try again
```

#### "Login not working"
```bash
# Check if auth views are properly set up
# Verify rest_framework is installed
# Check user model configuration
```

#### "Customer dashboard shows no data"
```
# Check if user is authenticated
# Verify API endpoints are accessible
# Check browser console for JavaScript errors
# Verify database has order data
```

---

## ✅ TESTING

### Manual Testing Checklist

- [ ] User registration works
- [ ] User login works
- [ ] Browsing products works
- [ ] **Add to cart** shows notification
- [ ] Cart count updates
- [ ] Cart page loads items
- [ ] Checkout process works
- [ ] Order created in database
- [ ] Customer dashboard loads
- [ ] Orders display correctly
- [ ] Can write review
- [ ] Can delete review
- [ ] Can view order details
- [ ] Tracking information displays
- [ ] Logout works

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test cart
python manage.py test orders

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # generates htmlcov/index.html
```

---

## 🔒 SECURITY CHECKLIST

Before going to production:

- [ ] Change `SECRET_KEY` to a unique value
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Enable HTTPS/SSL certificate
- [ ] Set strong database password
- [ ] Configure CORS properly
- [ ] Enable CSRF protection
- [ ] Set secure session cookies
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Enable security headers
- [ ] Regular backups configured
- [ ] Remove debug toolbar in production

### Security Headers to Add

```python
# In settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'"),
    'style-src': ("'self'", "'unsafe-inline'"),
}
X_FRAME_OPTIONS = 'DENY'
```

---

## 📊 MONITORING & MAINTENANCE

### Logging

```python
# In settings.py
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

### Backups

```bash
# Database backup (PostgreSQL)
pg_dump -U perfume_user perfume_db > backup.sql

# Media files backup
tar -czf media_backup.tar.gz media/

# Restore from backup
psql -U perfume_user perfume_db < backup.sql
```

### Monitoring Tools

- **Sentry** - Error tracking: https://sentry.io
- **New Relic** - Performance monitoring: https://newrelic.com
- **DataDog** - Infrastructure monitoring: https://www.datadoghq.com
- **Uptime Robot** - Uptime monitoring: https://uptimerobot.com

---

## 📁 PROJECT STRUCTURE

```
perfume_production/
├── perfume_platform/              # Django project
│   ├── perfume_platform/         # Main settings
│   │   ├── settings.py           # Django configuration
│   │   ├── urls.py               # URL routing
│   │   └── wsgi.py               # WSGI config
│   ├── accounts/                 # User authentication
│   │   ├── views.py              # Auth views
│   │   ├── dashboard_views.py    # Customer dashboard APIs
│   │   ├── urls.py               # Auth URLs
│   │   └── models.py             # User models
│   ├── catalog/                  # Products & brands
│   │   ├── models.py             # Product models
│   │   ├── views.py              # Product views
│   │   └── urls.py               # Catalog URLs
│   ├── cart/                     # Shopping cart
│   │   ├── models.py             # Cart models
│   │   ├── views.py              # Cart views
│   │   └── urls.py               # Cart URLs
│   ├── orders/                   # Order management
│   │   ├── models.py             # Order models
│   │   ├── views.py              # Order views
│   │   └── urls.py               # Order URLs
│   └── manage.py                 # Django CLI
├── templates/                    # HTML templates
│   ├── home.html                 # Homepage
│   ├── shop.html                 # Product listing
│   ├── cart.html                 # Shopping cart
│   ├── customer_dashboard.html   # PRODUCTION customer dashboard
│   ├── checkout.html             # Checkout
│   └── partials/                 # Reusable components
├── static/                       # CSS, JS, images
│   ├── css/                      # Stylesheets
│   ├── js/
│   │   ├── main.js              # PRODUCTION app JavaScript
│   │   ├── cart.js              # Cart functions
│   │   └── auth.js              # Auth functions
│   └── images/                   # Images
├── requirements.txt              # Python dependencies
├── Procfile                      # For Heroku
├── runtime.txt                   # Python version
└── README.md                     # Documentation
```

---

## 📞 SUPPORT & HELP

If you encounter issues:

1. **Check Documentation** - Read SETUP_AND_DEPLOYMENT.md
2. **Check Logs** - `python manage.py runserver --verbosity 2`
3. **Check Browser Console** - Press F12 to see JavaScript errors
4. **Check Network Tab** - See what API calls are being made
5. **Test Database** - `python manage.py dbshell`
6. **Test API** - Use curl or Postman to test endpoints

### Getting Help

```bash
# Show Django commands
python manage.py help

# Show specific command help
python manage.py help migrate

# Check Python packages
pip list

# Check virtual environment
which python  # or: where python (Windows)
```

---

## 🎉 YOU'RE READY!

Your premium e-commerce platform is:
✅ **Complete** - All features implemented
✅ **Tested** - Fully functional
✅ **Documented** - Clear instructions
✅ **Production-Ready** - Ready to deploy

**Next Step:** Choose a hosting platform and deploy!

---

**Last Updated:** August 2024  
**Version:** 2.0 - Production Complete  
**Status:** Ready for Production Deployment
