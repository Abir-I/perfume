# 🚀 QUICK START GUIDE - The Last Note E-Commerce

## ⚡ 5-Minute Setup

### Step 1: Extract Project
```bash
unzip perfume_final_fixed_COMPLETE.zip
cd perfume_final_fixed
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Setup Database
```bash
# Create database in MySQL
mysql -u root -p
> CREATE DATABASE perfume_platform CHARACTER SET utf8mb4;
> EXIT;

# Run migrations
cd perfume_platform
python manage.py migrate
```

### Step 4: Create Admin Account
```bash
python manage.py createsuperuser
# Follow prompts
```

### Step 5: Run Server
```bash
python manage.py runserver
```

### Step 6: Access Application
```
Frontend: http://127.0.0.1:8000
Admin: http://127.0.0.1:8000/admin/
API: http://127.0.0.1:8000/api/
```

---

## 📝 Database Credentials (Default)

Edit `perfume_platform/perfume_platform/settings.py` if different:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'perfume_platform',
        'USER': 'root',
        'PASSWORD': '',  # Add password here
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

## 🧪 Testing the Features

### 1. Registration & Login
1. Go to http://127.0.0.1:8000
2. Click "SIGN UP" 
3. Fill form and register
4. Login with credentials
5. ✅ User dashboard appears

### 2. Browse Products
1. Click "SHOP"
2. Browse products with filters
3. Filter by brand, price, concentration
4. ✅ Products display correctly

### 3. Add to Cart & Checkout
1. Click product
2. Click "Add to Cart"
3. Go to cart
4. Click "Proceed to Checkout"
5. Fill shipping address
6. Click "Place Order"
7. ✅ Order created, stock reduced

### 4. Check Stock Reduction
1. Go to admin: http://127.0.0.1:8000/admin/
2. Go to Catalog → Products
3. Check product quantity
4. ✅ Should be reduced from original

### 5. Cancel Order & Stock Restore
1. Go to Customer Dashboard
2. Click "My Orders"
3. Click order "Cancel"
4. Go to admin and check product quantity
5. ✅ Should be restored to previous level

### 6. Admin Management
1. Login as superuser
2. Go to admin panel
3. Add/edit/delete products
4. Manage brands, discounts
5. View and manage orders
6. ✅ All changes reflect on frontend

---

## 🔧 Configuration

### Important Settings in `settings.py`:

```python
# For Production
DEBUG = False  # Change to False
ALLOWED_HOSTS = ['yourdomain.com']
SECRET_KEY = 'generate-new-random-key'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'app-password'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'perfume_platform',
        'USER': 'root',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
    }
}
```

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'django'"
```bash
pip install -r requirements.txt
```

### "MySQL connection error"
```bash
# Check MySQL is running
mysql -u root -p
# Check database exists
SHOW DATABASES;
# Create if missing
CREATE DATABASE perfume_platform CHARACTER SET utf8mb4;
```

### "No tables in database"
```bash
cd perfume_platform
python manage.py migrate
```

### "Port 8000 already in use"
```bash
python manage.py runserver 8001
# Or kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### "Static files not loading"
```bash
python manage.py collectstatic --noinput
```

---

## 📁 Project Structure

```
perfume_final_fixed/
├── perfume_platform/          # Django project
│   ├── accounts/              # User management
│   ├── catalog/               # Products, brands, reviews
│   ├── cart/                  # Shopping cart
│   ├── orders/                # Orders, checkout, tracking
│   ├── perfume_platform/      # Settings, URLs, WSGI
│   ├── manage.py              # Django CLI
│   └── migrations/            # Database migrations
├── templates/                 # HTML templates
├── static/                    # CSS, JavaScript, images
├── media/                     # User uploads
├── requirements.txt           # Python dependencies
├── PROJECT_REPORT.md          # Detailed project report
├── BUG_FIXES_SUMMARY.md       # Bug fixes documentation
└── QUICK_START_FINAL.md       # This file
```

---

## 🌐 API Endpoints

### Authentication
```
POST /api/accounts/signup/
POST /api/accounts/login/
POST /api/accounts/logout/
POST /api/accounts/refresh/
```

### Products
```
GET /api/catalog/products/
GET /api/catalog/products/<id>/
GET /api/catalog/brands/
GET /api/catalog/brands/<id>/
```

### Cart
```
GET /api/cart/
POST /api/cart/add/
PATCH /api/cart/items/<id>/update/
DELETE /api/cart/items/<id>/remove/
DELETE /api/cart/clear/
```

### Orders
```
GET /api/orders/
GET /api/orders/<id>/
POST /api/orders/checkout/
POST /api/orders/<id>/cancel/
```

---

## 💾 Backup & Restore

### Backup Database
```bash
mysqldump -u root -p perfume_platform > backup.sql
```

### Restore Database
```bash
mysql -u root -p perfume_platform < backup.sql
```

### Backup Files
```bash
zip -r backup.zip perfume_final_fixed/
```

---

## 📊 Admin Tasks

### Add a Product
1. Go to http://127.0.0.1:8000/admin/
2. Catalog → Perfumes → Add Perfume
3. Fill all fields
4. Upload image
5. Set prices and discounts
6. Mark as featured if needed
7. Save
8. Then create Product variation

### Manage Stock
1. Admin → Catalog → Products
2. Click product
3. Adjust quantity
4. Save
5. Stock status updates automatically

### Create Offer
1. Admin → Catalog → Perfumes
2. Set discount_type and discount_value
3. Set discount_start and discount_end dates
4. Save
5. Appears as hot deal on frontend

### Process Order
1. Admin → Orders → Customer Orders
2. Click order
3. Change order_status
4. Add tracking number
5. Update tracked dates
6. Save

---

## 🚀 Deployment (Basic)

### Using Gunicorn
```bash
pip install gunicorn
gunicorn perfume_platform.wsgi:application --bind 0.0.0.0:8000
```

### Using Nginx (Basic Config)
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/static/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

---

## 🔐 Security Checklist

Before going live:
- [ ] Change SECRET_KEY
- [ ] Set DEBUG = False
- [ ] Update ALLOWED_HOSTS
- [ ] Configure CORS properly
- [ ] Setup HTTPS/SSL
- [ ] Use environment variables for secrets
- [ ] Run security checks: `python manage.py check --deploy`
- [ ] Update database password
- [ ] Enable CSRF_COOKIE_SECURE
- [ ] Enable SESSION_COOKIE_SECURE

---

## 📞 Common Commands

```bash
# Start server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create empty migration
python manage.py makemigrations --empty catalog

# Reset app (delete data)
python manage.py migrate catalog zero

# Run tests
python manage.py test

# Database shell
python manage.py shell

# Clear cache
python manage.py clear_cache
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Frontend loads without errors
- [ ] Can register new user
- [ ] Can login/logout
- [ ] Can browse products
- [ ] Can filter products
- [ ] Can add to cart
- [ ] Cart shows correct total
- [ ] Can proceed to checkout
- [ ] Order created successfully
- [ ] Stock reduced after order
- [ ] Can view order in dashboard
- [ ] Can cancel order
- [ ] Stock restored after cancel
- [ ] Admin panel accessible
- [ ] Can add product in admin
- [ ] Product appears on frontend
- [ ] Can edit product in admin
- [ ] Changes appear on frontend
- [ ] No console errors
- [ ] No database errors in logs

---

## 🎉 Ready to Go!

Your complete premium perfume e-commerce platform is now ready for use!

**Features Ready:**
- ✅ Full authentication system
- ✅ Product catalog with filters
- ✅ Shopping cart
- ✅ Checkout with stock management
- ✅ Order tracking
- ✅ Customer dashboard
- ✅ Admin panel
- ✅ Inventory management
- ✅ Security features

**Happy selling!** 🎀

For detailed information, see:
- `PROJECT_REPORT.md` - Full feature list and documentation
- `BUG_FIXES_SUMMARY.md` - What was fixed
- Code comments - Inline documentation

---

## 📧 Questions?

Refer to:
1. Django docs: https://docs.djangoproject.com/
2. DRF docs: https://www.django-rest-framework.org/
3. Project code comments
4. This guide's troubleshooting section

Enjoy! 🎀
