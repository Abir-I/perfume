# The Last Note — Final Unit Testing Guide

## What is included

This build contains a deterministic Django unit-test suite with **364 tests**:

- Positive / expected-success tests: listed in `ALL_TESTS.txt`
- Negative / validation/security tests: listed in `ALL_TESTS.txt`
- Accounts: registration validation, password boundaries, duplicate-email protection, admin permission rules
- Catalog: image URL normalization, notes, stock states, slugs/URLs, gallery fallback, reviews, serializers, wishlist/recently-viewed helpers
- Cart: quantity validation, inactive/unknown product rejection, subtotal/total calculations
- Orders: status matrix, valid/invalid transitions, cancellation/delivery side effects, checkout validation
- COD-related checkout input behavior

## Why the previous suite failed

The earlier suite incorrectly used `SimpleTestCase` for tests that reached the ORM. Django therefore reported `DatabaseOperationForbidden`. The registration serializer's `validate_email()` performs a `User.objects.filter(...)` lookup, and the order service is wrapped in `transaction.atomic`; both caused the previous failures.

This final suite fixes the **test design**, not by hiding failures, but by mocking database managers for serializer/unit-helper tests and using the wrapped order-service function only for deterministic transition logic. The production MySQL database is not required for this unit suite.

## Install

From the project root:

### Windows CMD

```bat
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-test.txt
```

### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-test.txt
```

## Run the complete suite

```bat
cd perfume_platform
python manage.py test accounts.test_unit_suite catalog.test_unit_suite cart.test_unit_suite orders.test_unit_suite --verbosity 2
```

Or use Django discovery:

```bat
python manage.py test --verbosity 2
```

## Run only negative tests

Django does not provide a native "negative" label, so use the class names shown in `ALL_TESTS.txt`, for example:

```bat
python manage.py test accounts.test_unit_suite.AccountPermissionUnitTests
python manage.py test accounts.test_unit_suite.RegisterSerializerUnitTests
python manage.py test catalog.test_unit_suite.ImageNormalizationNegativeTests
python manage.py test cart.test_unit_suite.AddCartItemValidationUnitTests
python manage.py test orders.test_unit_suite.OrderServiceNegativeTests
python manage.py test orders.test_unit_suite.CheckoutSerializerNegativeTests
```

## Coverage

```bat
python -m pip install -r requirements-test.txt
python -m coverage erase
python -m coverage run --source=accounts,catalog,cart,orders manage.py test accounts.test_unit_suite catalog.test_unit_suite cart.test_unit_suite orders.test_unit_suite
python -m coverage report -m
python -m coverage html
```

Open `htmlcov\index.html` after the command completes.

## Recommended acceptance result

The unit suite should finish with:

```text
Ran 364 tests in ...
OK
```

If Django reports an environment/dependency error before running tests, fix the environment first. A test failure after the suite starts should be investigated rather than ignored.

## What unit tests do NOT replace

After the unit suite passes, perform a manual/integration pass against the real database for:

1. Admin: add/edit/delete Brand.
2. Admin: add/edit/delete Perfume.
3. Admin: upload/replace/remove perfume images.
4. Admin: add/edit Product Variants (volume, price, stock).
5. Customer: registration/login/logout.
6. Customer: homepage/shop/product-detail image loading.
7. Customer: filters and search.
8. Customer: wishlist and recently viewed.
9. Customer: cart and quantity/stock behavior.
10. Customer: COD checkout and order creation.
11. Customer: order history/status/cancellation rules.
12. Admin: order status management.

The unit suite intentionally does not mutate or depend on your production MySQL data.

## Complete test inventory

See `ALL_TESTS.txt` for the name of every included positive and negative test.
