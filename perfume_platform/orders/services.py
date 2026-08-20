from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.models import CustomerOrder, OrderItem, Payment, Invoice
from .models import OrderStatus, OrderStatusHistory


ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


@transaction.atomic
def advance_order_status(order, new_status, changed_by=None, note=""):
    old_status = order.status
    if old_status == new_status:
        raise ValidationError("Order status is already set.")

    if new_status not in {s.value for s in OrderStatus}:
        raise ValidationError("Invalid order status.")

    if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
        raise ValidationError(f"Invalid status transition: {old_status} → {new_status}.")

    if new_status == OrderStatus.CANCELLED:
        for item in OrderItem.objects.select_related("product").filter(order=order):
            product = item.product
            product.stock_quantity += item.quantity
            if product.stock_quantity > 0:
                product.is_active = 1
            product.save(update_fields=["stock_quantity", "is_active"])
        Invoice.objects.filter(order=order).update(status="Cancelled")
    elif new_status == OrderStatus.DELIVERED:
        Payment.objects.filter(order=order).update(status="Completed")
        Invoice.objects.filter(order=order).update(status="Paid")

    order.status = new_status
    order.save(update_fields=["status"])

    OrderStatusHistory.objects.create(
        order=order,
        status=new_status,
        changed_by=changed_by,
        note=note or f"Status changed from {old_status} to {new_status}",
    )

    return new_status
