"""
Cart Models
Manages shopping cart for users
"""

from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product


class Cart(models.Model):
    """Shopping cart for user"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart_cart'
    
    def __str__(self):
        return f"Cart for {self.user.username if self.user else 'Guest'}"
    
    def get_total_price(self):
        """Calculate total price of all items"""
        items = self.items.all()
        total = sum(item.get_subtotal() for item in items)
        return total
    
    def get_total_items(self):
        """Get total number of items"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0


class CartItem(models.Model):
    """Individual items in cart"""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_cart_item'
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.product.perfume.perfume_name} x {self.quantity}"
    
    def get_subtotal(self):
        """Get subtotal for this item"""
        # Use final_price if available (with discount), else use base price
        price = getattr(self.product.perfume, 'final_price', None) or self.product.price
        return float(price) * self.quantity


class Coupon(models.Model):
    """Discount coupons"""
    
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.IntegerField(default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.IntegerField(null=True, blank=True)
    times_used = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'cart_coupon'
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        """Check if coupon is still valid"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.times_used < self.usage_limit)
        )
