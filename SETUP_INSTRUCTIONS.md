# Cart Feature Package

Adds "view cart" + "add item to cart" for logged-in customers, with
server-side rejection of zero/negative/invalid quantities.

## 1. Copy these files into your project

Copy everything under `perfume_platform/` in this package into your
project's `perfume_platform/` folder, keeping the same paths:

```
perfume_platform/accounts/authentication.py   <- new file
perfume_platform/cart/__init__.py             <- new app
perfume_platform/cart/apps.py
perfume_platform/cart/migrations/__init__.py
perfume_platform/cart/serializers.py
perfume_platform/cart/urls.py
perfume_platform/cart/views.py
```

None of these overwrite anything you already have — `cart/` is a brand
new app, and `accounts/authentication.py` is a new file inside your
existing `accounts` app.

## 2. Edit `perfume_platform/perfume_platform/settings.py`

Add `'cart'` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'accounts',
    'cart',          # <-- add this line
]
```

## 3. Edit `perfume_platform/perfume_platform/urls.py`

Mount the cart app's URLs:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/cart/', include('cart.urls')),   # <-- add this line
]
```

## 4. No migrations needed

`cart` doesn't define any new models — it reuses `Cart`, `CartItem`,
and `Product` from `accounts/models.py`, which already map to your
existing `cart`, `cart_item`, and `product` tables (`managed = False`).
Nothing to run against the database.

## 5. Try it out

Log in first to get an access token from your existing
`POST /api/accounts/login/`, then:

**View cart**
```
GET /api/cart/
Authorization: Bearer <access_token>
```

**Add an item**
```
POST /api/cart/items/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_id": 5,
  "quantity": 2
}
```

Sending `"quantity": 0` or `"quantity": -3` returns a `400` with a
clear validation message instead of touching the database.

## Why `accounts/authentication.py` is needed

Your `LoginView` issues JWTs against your own `user` table, but DRF's
default `JWTAuthentication` resolves `request.user` against Django's
*built-in* auth table (since `AUTH_USER_MODEL` was never set) — a
mismatch that breaks any endpoint requiring `IsAuthenticated`. The
cart views use `CustomJWTAuthentication` from this new file instead,
which resolves tokens against your actual `accounts.User` table. Any
other endpoint you protect later will need the same authentication
class.
