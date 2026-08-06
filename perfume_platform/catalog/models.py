"""
Catalog Models - Complete Product, Brand, Perfume
"""

from django.db import models


class Brand(models.Model):
    """Perfume Brand"""
    
    brand_id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    country = models.CharField(max_length=50, blank=True)
    established_year = models.IntegerField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'brand'
        ordering = ['brand_name']
    
    def __str__(self):
        return self.brand_name


class Perfume(models.Model):
    """Perfume Product"""
    
    perfume_id = models.AutoField(primary_key=True)
    perfume_name = models.CharField(max_length=200, unique=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='perfumes')
    description = models.TextField()
    image = models.ImageField(upload_to='perfumes/')
    
    # Concentration
    concentration = models.CharField(
        max_length=20,
        choices=[
            ('EDT', 'Eau de Toilette'),
            ('EDP', 'Eau de Parfum'),
            ('Parfum', 'Parfum'),
            ('EDC', 'Eau de Cologne'),
        ],
        default='EDT'
    )
    
    # Size
    size = models.CharField(
        max_length=20,
        choices=[
            ('decant', 'Decant'),
            ('full_size', 'Full Size'),
        ],
        default='full_size'
    )
    
    # Gender
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('unisex', 'Unisex'),
        ],
        default='unisex'
    )
    
    # Season
    season = models.CharField(
        max_length=20,
        choices=[
            ('spring', 'Spring'),
            ('summer', 'Summer'),
            ('autumn', 'Autumn'),
            ('winter', 'Winter'),
            ('all_season', 'All Season'),
        ],
        default='all_season'
    )
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Discount
    discount_type = models.CharField(
        max_length=20,
        choices=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed'),
            ('none', 'None'),
        ],
        default='none'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_start = models.DateTimeField(blank=True, null=True)
    discount_end = models.DateTimeField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Limited Edition
    is_limited_edition = models.BooleanField(default=False)
    limited_quantity = models.IntegerField(blank=True, null=True)
    limited_sold = models.IntegerField(default=0)
    
    # Marketing
    is_featured = models.BooleanField(default=False)
    is_hot_deal = models.BooleanField(default=False)
    offer_description = models.TextField(blank=True)
    offer_end_date = models.DateTimeField(blank=True, null=True)
    
    # Stock
    stock_status = models.CharField(
        max_length=20,
        choices=[
            ('in_stock', 'In Stock'),
            ('low_stock', 'Low Stock'),
            ('out_of_stock', 'Out of Stock'),
            ('pre_order', 'Pre Order'),
            ('discontinued', 'Discontinued'),
        ],
        default='in_stock'
    )
    low_stock_threshold = models.IntegerField(default=10)
    pre_order_date = models.DateTimeField(blank=True, null=True)
    allow_backorder = models.BooleanField(default=False)
    reorder_level = models.IntegerField(default=5)
    warehouse = models.CharField(max_length=100, blank=True)
    
    # Tags & Category
    tags = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, blank=True)
    sub_category = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    review_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'perfume'
        indexes = [
            models.Index(fields=['brand']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['stock_status']),
        ]
    
    def __str__(self):
        return self.perfume_name
    
    def save(self, *args, **kwargs):
        """Calculate final price"""
        if self.discount_type == 'none':
            self.final_price = self.base_price
        elif self.discount_type == 'percentage':
            discount = (self.base_price * self.discount_value) / 100
            self.final_price = self.base_price - discount
        elif self.discount_type == 'fixed':
            self.final_price = self.base_price - self.discount_value
        
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product (Perfume variation)"""
    
    product_id = models.AutoField(primary_key=True)
    perfume = models.ForeignKey(Perfume, on_delete=models.CASCADE, related_name='products')
    
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    
    product_type = models.CharField(
        max_length=20,
        choices=[
            ('decant', 'Decant'),
            ('full_size', 'Full Size'),
            ('sample', 'Sample'),
        ],
        default='full_size'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product'
        unique_together = ['perfume', 'product_type']
        indexes = [
            models.Index(fields=['perfume']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.perfume.perfume_name} - {self.product_type}"


class Review(models.Model):
    """Product Review"""
    
    review_id = models.AutoField(primary_key=True)
    perfume = models.ForeignKey(Perfume, on_delete=models.CASCADE, related_name='reviews')
    user_name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.perfume.perfume_name} - {self.rating}★"
