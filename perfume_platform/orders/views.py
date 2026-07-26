from decimal import Decimal

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Address, Cart, CustomerOrder, Product

from .serializers import CheckoutSerializer, OrderDetailSerializer, OrderListItemSerializer

# customer_order.status is a MySQL ENUM('Pending','Confirmed','Processing',
# 'Shipped','Delivered','Cancelled') - there is no 'Paid' value in the
# schema. Payment success is tracked separately in the `payment` table.
# Lookup is case-insensitive so API clients can send lowercase
# ("pending", "shipped", ...) and still match the real enum value.
ORDER_STATUSES = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
STATUS_LOOKUP = {value.lower(): value for value in ORDER_STATUSES}

# Checkout math: subtotal (sum of line items) + tax + shipping = total_amount.
# customer_order only stores one total_amount column (see perfume.sql), so
# tax/shipping are computed here and returned in the response, not stored
# as separate DB columns. Both default to 0 - set real business values in
# settings.py (ORDER_TAX_RATE, ORDER_FLAT_SHIPPING_FEE) once known.
TAX_RATE = getattr(settings, 'ORDER_TAX_RATE', Decimal('0.00'))
FLAT_SHIPPING_FEE = getattr(settings, 'ORDER_FLAT_SHIPPING_FEE', Decimal('0.00'))


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
      1. creates the order row (subtotal + tax + shipping = total_amount)
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

        subtotal = sum(
            (item.quantity * locked_products[item.product_id].price for item in cart_items),
            Decimal('0.00'),
        )
        tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'))
        shipping = FLAT_SHIPPING_FEE
        total_amount = subtotal + tax + shipping

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
                "line_total": str(item.quantity * unit_price),
            })

        cart.cartitem_set.all().delete()
        cart.updated_at = timezone.now()
        cart.save(update_fields=['updated_at'])

        return {
            "order_id": order.order_id,
            "status": order.status,
            "order_date": order.order_date,
            "subtotal": str(subtotal),
            "tax": str(tax),
            "shipping": str(shipping),
            "total_amount": str(order.total_amount),
            "address_id": address.address_id,
            "notes": order.notes,
            "items": items_out,
        }


class OrderDetailView(APIView):
    """
    GET /api/orders/{order_id}/
    Returns items, status, total, date, and shipping address for one order.
    Only ever returns an order that belongs to the logged-in customer - any
    other order_id (yours or someone else's that doesn't exist) is a 404.
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = CustomerOrder.objects.select_related('address').get(
                order_id=order_id, user=request.user,
            )
        except CustomerOrder.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_200_OK)


class OrderListView(APIView):
    """
    GET /api/orders/
    Returns the logged-in customer's own orders, newest first, paginated.

    Query params:
      - status:    optional, case-insensitive (pending/confirmed/processing/
                   shipped/delivered/cancelled). There is no "paid" status
                   in the schema - see ORDER_STATUSES above.
      - page:      default 1
      - page_size: default 10, max 50
    """
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = CustomerOrder.objects.filter(user=request.user).order_by('-order_date')

        status_param = request.query_params.get('status')
        if status_param:
            matched_status = STATUS_LOOKUP.get(status_param.strip().lower())
            if matched_status is None:
                return Response(
                    {
                        "error": f"'{status_param}' is not a valid order status.",
                        "valid_statuses": ORDER_STATUSES,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            orders = orders.filter(status=matched_status)

        try:
            page = max(int(request.query_params.get('page', 1)), 1)
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = min(max(int(request.query_params.get('page_size', 10)), 1), 50)
        except (TypeError, ValueError):
            page_size = 10

        total_count = orders.count()
        start = (page - 1) * page_size
        page_of_orders = orders[start:start + page_size]
        num_pages = (total_count + page_size - 1) // page_size if total_count else 0

        return Response({
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "num_pages": num_pages,
            "results": OrderListItemSerializer(page_of_orders, many=True).data,
        }, status=status.HTTP_200_OK)
