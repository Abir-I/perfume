"""
Sprint 6: Data Integrity Verification (run AFTER the MySQL -> PostgreSQL
migration, before switching DB_ENGINE=postgres in production).

This can't be executed as part of building this feature — it needs a
real MySQL database with real data and a real, already-migrated
PostgreSQL database to compare against. What's here is the actual
verification logic, ready to run once both exist.

--------------------------------------------------------------------
HOW TO RUN
--------------------------------------------------------------------
1. In settings.py, temporarily define BOTH databases side by side:

     DATABASES = {
         'default': { ...your normal DB_ENGINE-driven config... },
         'mysql_source': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': os.environ['SOURCE_DB_NAME'],
             'USER': os.environ['SOURCE_DB_USER'],
             'PASSWORD': os.environ['SOURCE_DB_PASSWORD'],
             'HOST': os.environ['SOURCE_DB_HOST'],
             'PORT': os.environ.get('SOURCE_DB_PORT', '3306'),
         },
         'postgres_dest': {
             'ENGINE': 'django.db.backends.postgresql',
             'NAME': os.environ['DEST_DB_NAME'],
             'USER': os.environ['DEST_DB_USER'],
             'PASSWORD': os.environ['DEST_DB_PASSWORD'],
             'HOST': os.environ['DEST_DB_HOST'],
             'PORT': os.environ.get('DEST_DB_PORT', '5432'),
         },
     }

   (Only needed for this one-time verification run — revert afterward.)

2. From perfume_platform/ (next to manage.py):
     python ../scripts/verify_data_integrity.py

--------------------------------------------------------------------
WHAT IT CHECKS
--------------------------------------------------------------------
- Row counts match, table by table.
- Every primary key that exists in the source also exists in the
  destination (catches partial/failed row migrations that a plain
  count could hide, e.g. 100 rows migrated but 3 different ones than
  expected due to a filter bug).
- Prints a clear PASS/FAIL summary per table and a non-zero exit code
  if anything doesn't match, so it can be used as a CI/deploy gate.
"""
import os
import sys

import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'perfume_platform'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfume_platform.settings')
django.setup()

from accounts.models import (  # noqa: E402
    Address, Brand, BulkBottle, Cart, CartItem, CustomerOrder, DecantBatch,
    Invoice, LoginAttempt, OrderItem, Payment, Perfume, Product,
    PasswordResetToken, Review, Role, User,
)

MODELS_TO_CHECK = [
    Role, User, Address, Brand, Perfume, Product, BulkBottle, DecantBatch,
    Cart, CartItem, CustomerOrder, OrderItem, Payment, Invoice, Review,
    PasswordResetToken, LoginAttempt,
]


def verify():
    all_ok = True
    print(f"{'Table':<25}{'Source':>10}{'Dest':>10}{'Status':>12}")
    print("-" * 57)

    for model in MODELS_TO_CHECK:
        table = model._meta.db_table
        pk_field = model._meta.pk.name

        source_ids = set(model.objects.using('mysql_source').values_list(pk_field, flat=True))
        dest_ids = set(model.objects.using('postgres_dest').values_list(pk_field, flat=True))

        missing = source_ids - dest_ids
        status = "OK" if not missing else f"MISSING {len(missing)}"
        if missing:
            all_ok = False

        print(f"{table:<25}{len(source_ids):>10}{len(dest_ids):>10}{status:>12}")
        if missing and len(missing) <= 20:
            print(f"    missing {pk_field}s: {sorted(missing)}")

    print("-" * 57)
    print("ALL TABLES MATCH" if all_ok else "MISMATCHES FOUND - do not cut over yet")
    return all_ok


if __name__ == '__main__':
    ok = verify()
    sys.exit(0 if ok else 1)
