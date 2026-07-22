# Checkout Feature Package

Turns the logged-in customer's cart into a real order. All the writes
(order, order items, stock deduction, emptying the cart) happen inside
one database transaction, so it's all-or-nothing: if anything goes
wrong partway through, nothing is saved and the cart is untouched.

**Requires the `cart` feature package (and `accounts/authentication.py`)
to already be in your project** — checkout reads from the same `Cart`
that feature adds. If you haven't added that one yet, add it first.

## 1. Copy these files into your project

Copy everything under `perfume_platform/` in this package into your
project's `perfume_platform/` folder, keeping the same paths:

```
perfume_platform/orders/__init__.py             <- new app
perfume_platform/orders/apps.py
perfume_platform/orders/migrations/__init__.py
perfume_platform/orders/serializers.py
perfume_platform/orders/views.py
perfume_platform/orders/urls.py
```

`orders/` is a brand new app — nothing existing gets overwritten.

## 2. Edit `perfume_platform/perfume_platform/settings.py`

Add `'orders'` to `INSTALLED_APPS`:

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
    'cart',
    'orders',        # <-- add this line
]
```

## 3. Edit `perfume_platform/perfume_platform/urls.py`

Mount the orders app's URLs:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),   # <-- add this line
]
```

## 4. No migrations needed

`orders` doesn't define any new models — it reuses `CustomerOrder`,
`Address`, `Cart`, and `Product` from `accounts/models.py`, which
already map to your existing `order`, `address`, `cart`, and `product`
tables (`managed = False`). Nothing to run against the database.

## 5. Try it out

Log in, add something to your cart, make sure the account has at
least one address in the `address` table, then:

```
POST /api/orders/checkout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "address_id": 3,
  "notes": "Leave at the front desk"
}
```

Success (`201`) returns the created order with its line items. The
cart is now empty and each product's stock has been reduced.

If something's wrong — the address isn't yours, the cart is empty, or
an item doesn't have enough stock left — you get a `400` with details,
and **nothing was written to the database**: no order, no order items,
no stock change, cart untouched.

## How the all-or-nothing part works

`orders/views.py` does the actual order + order-item creation + stock
deduction + cart clearing inside a method wrapped in
`@transaction.atomic`. If any step raises an exception — including a
deliberate `CheckoutError` when stock turns out to be insufficient —
Django rolls back every database write made inside that block before
the exception is handled. The view catches that error outside the
transaction and turns it into a clean `400` response, so a failed
checkout never leaves a half-created order, missing stock, or an
emptied cart behind.

It also uses `select_for_update()` to lock the relevant product rows
for the duration of the transaction, so two customers checking out at
the exact same moment can't both "succeed" in buying the last unit of
something.

One implementation detail worth knowing: `order_item.subtotal` in your
database is a MySQL `GENERATED ALWAYS ... STORED` column (MySQL
computes it itself from `quantity * unit_price`). Because of that,
order items are inserted with a small raw SQL statement instead of the
ORM's normal `.create()`, since generated columns can't be named in an
INSERT. That insert still runs on the same connection/transaction as
everything else, so it rolls back along with everything else if the
checkout fails.
