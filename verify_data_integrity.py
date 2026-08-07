
import os
import sys

import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'perfume_platform'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfume_platform.settings')
django.setup()

from accounts.models import (  
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
