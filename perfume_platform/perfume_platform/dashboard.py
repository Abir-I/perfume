import json
from datetime import timedelta

from django.db.models import Avg, Count, F, Sum
from django.utils import timezone

from accounts.models import CustomerOrder, OrderItem, Product, Review, User


def dashboard_callback(request, context):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    paid = CustomerOrder.objects.exclude(status="Cancelled")

    context.update({
        "kpis": [
            {"label": "Revenue this month",
             "value": f"৳{paid.filter(order_date__gte=month_start).aggregate(t=Sum('total_amount'))['t'] or 0:,.0f}"},
            {"label": "Orders today",
             "value": CustomerOrder.objects.filter(order_date__gte=now - timedelta(days=1)).count()},
            {"label": "Pending orders",
             "value": CustomerOrder.objects.filter(status="Pending").count()},
            {"label": "Customers",
             "value": User.objects.filter(is_active=1).count()},
        ],
        "status_breakdown": list(
            CustomerOrder.objects.values("status").annotate(n=Count("order_id")).order_by("-n")
        ),
        "low_stock": list(
            Product.objects.select_related("perfume", "perfume__brand")
            .filter(is_active=1, stock_quantity__lt=5)
            .order_by("stock_quantity")[:8]
        ),
        "recent_orders": list(
            CustomerOrder.objects.select_related("user").order_by("-order_date")[:8]
        ),
        "pending_reviews": Review.objects.count(),
        "aov": paid.aggregate(a=Avg("total_amount"))["a"] or 0,
        "returning_customers": (
            paid.values("user_id").annotate(n=Count("order_id")).filter(n__gt=1).count()
        ),
        "best_sellers": list(
            OrderItem.objects.values(
                name=F("product__perfume__perfume_name"), ml=F("product__volume_ml")
            )
            .annotate(sold=Sum("quantity"), revenue=Sum("subtotal"))
            .order_by("-sold")[:5]
        ),
    })

    months, revenue = [], []
    for i in range(5, -1, -1):
        start = (month_start - timedelta(days=31 * i)).replace(day=1)
        end = (start + timedelta(days=31)).replace(day=1)
        months.append(start.strftime("%b"))
        revenue.append(float(
            paid.filter(order_date__gte=start, order_date__lt=end)
                .aggregate(t=Sum("total_amount"))["t"] or 0
        ))

    context["revenue_chart"] = json.dumps({
        "labels": months,
        "datasets": [{
            "label": "Revenue",
            "data": revenue,
            "backgroundColor": "var(--color-primary-500)",
            "borderRadius": 4,
        }],
    })

    return context
