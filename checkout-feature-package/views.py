from decimal import Decimal

from django.db import connection, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Address, Cart, CustomerOrder, Product

from .serializers import CheckoutSerializer


class CheckoutError(Exception):
    """
    Raised to deliberately abort a checkout in progress.

    It's always raised from *inside* the @transaction.atomic block in
    _place_order, so Django rolls back every write that block made before
    re-raising it up to post(), where it's turned into a clean 400. That's
    what makes checkout all-or-nothing: nothing partial is ever left behind.
    """
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


def _insert_order_item(order_id, product_id, quantity, unit_price):
    # order_item.subtotal is a MySQL GENERATED ALWAYS ... STORED column
    # (quantity * unit_price computed by MySQL itself). It must never be
    # named in the INSERT column list, so this bypasses the ORM's normal
    # create() - which would try to insert it - and writes the four real
    # columns directly. This still runs on the connection's current
    # transaction, so it's covered by the same atomic() rollback as
    # everything else in _place_order.
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO order_item (order_id, product_id, quantity, unit_price) "
            "VALUES (%s, %s, %s, %s)",
            [order_id, product_id, quantity, unit_price],
        )


class CheckoutView(APIView):
    """
    POST /api/orders/checkout/
    Body: {"address_id": 3, "notes": "optional"}

    Turns the logged-in customer's current cart into a real order:
      1. creates the order row
      2. creates one order_item row per cart item
      3. deducts each product's stock
      4. empties the cart

    All four steps happen inside one database transaction. If any step
    fails for any reason - a bad address, an item that just went out of
    stock, a database error, anything - everything done in this request
    is rolled back: no order, no order items, no stock changes, and the
    cart is left exactly as it was. It's all or nothing.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        address_id = serializer.validated_data['address_id']
        notes = serializer.validated_data.get('notes', '')

        try:
            address = Address.objects.get(address_id=address_id, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {"error": "That address doesn't exist on your account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = list(cart.cartitem_set.select_related('product').all())
        if not cart_items:
            return Response({"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = self._place_order(request.user, address, notes, cart, cart_items)
        except CheckoutError as exc:
            return Response({"error": exc.message, **exc.details}, status=status.HTTP_400_BAD_REQUEST)

        return Response(order, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def _place_order(self, user, address, notes, cart, cart_items):
        # Lock the exact product rows we're about to sell for the rest of
        # this transaction, so a second checkout running at the same
        # moment can't also decide there's enough stock for the same units.
        product_ids = [item.product_id for item in cart_items]
        locked_products = {
            p.product_id: p
            for p in Product.objects.select_for_update().filter(product_id__in=product_ids)
        }

        problems = []
        for item in cart_items:
            product = locked_products.get(item.product_id)
            if product is None or not product.is_active:
                problems.append({"product_id": item.product_id, "issue": "no longer available"})
            elif product.stock_quantity < item.quantity:
                problems.append({
                    "product_id": item.product_id,
                    "issue": "not enough stock",
                    "requested": item.quantity,
                    "available": product.stock_quantity,
                })

        if problems:
            # Abort before anything is written. Everything below this
            # point only runs once every line item has been checked.
            raise CheckoutError(
                "Some items in your cart can't be ordered right now.",
                {"problems": problems},
            )

        total_amount = sum(
            (item.quantity * locked_products[item.product_id].price for item in cart_items),
            Decimal('0.00'),
        )

        order = CustomerOrder.objects.create(
            user=user,
            address=address,
            order_date=timezone.now(),
            status='Pending',
            total_amount=total_amount,
            notes=notes,
        )

        items_out = []
        for item in cart_items:
            product = locked_products[item.product_id]
            unit_price = product.price

            _insert_order_item(order.order_id, product.product_id, item.quantity, unit_price)

            product.stock_quantity -= item.quantity
            product.save(update_fields=['stock_quantity'])

            items_out.append({
                "product_id": product.product_id,
                "quantity": item.quantity,
                "unit_price": str(unit_price),
                "subtotal": str(item.quantity * unit_price),
            })

        cart.cartitem_set.all().delete()
        cart.updated_at = timezone.now()
        cart.save(update_fields=['updated_at'])

        return {
            "order_id": order.order_id,
            "status": order.status,
            "order_date": order.order_date,
            "total_amount": str(order.total_amount),
            "address_id": address.address_id,
            "notes": order.notes,
            "items": items_out,
        }
