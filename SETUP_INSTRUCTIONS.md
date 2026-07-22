<<<<<<< HEAD
# Auth & Input-Validation Hardening Package

**Requires the `cart` and `checkout` packages to already be in your
project** (and the `accounts/authentication.py` file that came with
the cart package).

## What this actually changes

Your cart and checkout endpoints already required a logged-in user and
already validated their input (quantity checks, product/address
existence, stock checks) - that was built into those two packages.
This package closes two gaps around them:

1. **Defense-in-depth on "logged-in only."** Until now, each view had
   to remember to declare `permission_classes = [IsAuthenticated]`
   itself. This package makes `IsAuthenticated` the **project-wide
   default**, so any endpoint added later that forgets to declare a
   permission is protected automatically instead of silently defaulting
   to open. `RegisterView` and `LoginView` are updated to explicitly opt
   out with `AllowAny`, since those two have to work while logged out.

2. **The same request.user fix, everywhere.** The `CustomJWTAuthentication`
   class from the cart package (which resolves tokens against your real
   `accounts.User` table instead of Django's unused built-in one) is now
   the project-wide default authentication class too - not just something
   cart/orders opted into individually.

3. **Consistent, safe error responses for broken input.** A new
   exception handler makes every kind of bad request - missing/expired
   token, invalid or missing fields, hitting a route that doesn't exist,
   even an unexpected server error - come back as the same predictable
   shape instead of Django's HTML debug page or a raw stack trace:
   ```json
   {"error": "Authentication credentials were not provided."}
   ```
   ```json
   {"error": "Invalid request.", "details": {"quantity": ["Quantity must be a positive whole number greater than zero."]}}
   ```

## 1. Copy these files into your project

```
perfume_platform/accounts/exception_handler.py   <- new file
perfume_platform/accounts/views.py               <- replaces your existing one
```

`views.py` is a full replacement of the file from your `accounts` app -
it's the same `RegisterView`/`LoginView` you have now, just with
`permission_classes = [AllowAny]` added to each.

## 2. Edit `perfume_platform/perfume_platform/settings.py`

Replace your `REST_FRAMEWORK` block with:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'accounts.authentication.CustomJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'accounts.exception_handler.custom_exception_handler',
}
```

That's the only settings change - `INSTALLED_APPS` and `urls.py` don't
need anything new for this package.

## 3. No migrations needed

Nothing here touches models or the database.

## 4. Try it out

- Hit `/api/cart/` or `/api/orders/checkout/` with **no** `Authorization`
  header → `401` with `{"error": "Authentication credentials were not
  provided."}` instead of a Django error page.
- Hit `/api/cart/items/` with `{"quantity": -1}` → `400` with a clean
  `{"error": "Invalid request.", "details": {...}}` body.
- `/api/accounts/register/` and `/api/accounts/login/` still work with
  no token, exactly as before.
=======
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
>>>>>>> e3386a4d74ddeeb9a881026351c901dd539fa312
