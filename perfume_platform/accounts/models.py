# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100)
    is_default = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'address'


class AuditLog(models.Model):
    audit_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    action_type = models.CharField(max_length=100)
    table_affected = models.CharField(max_length=100)
    record_id = models.IntegerField(blank=True, null=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    performed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'audit_log'


class Brand(models.Model):
    brand_id = models.AutoField(primary_key=True)
    brand_name = models.CharField(unique=True, max_length=150)
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'brand'


class BulkBottle(models.Model):
    bottle_id = models.AutoField(primary_key=True)
    perfume = models.ForeignKey('Perfume', models.DO_NOTHING)
    batch_number = models.CharField(unique=True, max_length=100)
    purchase_date = models.DateField()
    bottle_size_ml = models.DecimalField(max_digits=8, decimal_places=2)
    ml_remaining = models.DecimalField(max_digits=8, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier_name = models.CharField(max_length=200, blank=True, null=True)
    authenticity_verified = models.IntegerField()
    verification_notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bulk_bottle'


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('User', models.DO_NOTHING)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'cart'


class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, models.DO_NOTHING)
    product = models.ForeignKey('Product', models.DO_NOTHING)
    quantity = models.IntegerField()
    added_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'cart_item'
        unique_together = (('cart', 'product'),)


class ChatbotLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    session_id = models.CharField(max_length=100)
    user_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'chatbot_log'


class CustomerOrder(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    address = models.ForeignKey(Address, models.DO_NOTHING)
    order_date = models.DateTimeField()
    status = models.CharField(max_length=10)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customer_order'


class DecantBatch(models.Model):
    decant_batch_id = models.AutoField(primary_key=True)
    bottle = models.ForeignKey(BulkBottle, models.DO_NOTHING)
    product = models.ForeignKey('Product', models.DO_NOTHING)
    quantity_created = models.IntegerField()
    quantity_sold = models.IntegerField()
    date_created = models.DateTimeField()
    created_by = models.ForeignKey('User', models.DO_NOTHING, db_column='created_by')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'decant_batch'


class Faq(models.Model):
    faq_id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=100)
    question = models.CharField(max_length=500)
    answer = models.TextField()
    is_active = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'faq'


class Invoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(CustomerOrder, models.DO_NOTHING)
    invoice_number = models.CharField(unique=True, max_length=50)
    issued_date = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=9)

    class Meta:
        managed = False
        db_table = 'invoice'


class LoginAttempt(models.Model):
    attempt_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True)
    email_used = models.CharField(max_length=255)
    ip_address = models.CharField(max_length=45)
    was_successful = models.IntegerField()
    attempted_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'login_attempt'


class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(CustomerOrder, models.DO_NOTHING)
    product = models.ForeignKey('Product', models.DO_NOTHING)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_item'


class PasswordResetToken(models.Model):
    token_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    token_hash = models.CharField(unique=True, max_length=255)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'password_reset_token'


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    order = models.OneToOneField(CustomerOrder, models.DO_NOTHING)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=13)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=9)

    class Meta:
        managed = False
        db_table = 'payment'


class Perfume(models.Model):
    perfume_id = models.AutoField(primary_key=True)
    brand = models.ForeignKey(Brand, models.DO_NOTHING)
    perfume_name = models.CharField(max_length=200)
    concentration = models.CharField(max_length=7)
    top_notes = models.CharField(max_length=255, blank=True, null=True)
    middle_notes = models.CharField(max_length=255, blank=True, null=True)
    base_notes = models.CharField(max_length=255, blank=True, null=True)
    longevity_hours = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    sillage = models.CharField(max_length=8, blank=True, null=True)
    recommended_season = models.CharField(max_length=10, blank=True, null=True)
    target_gender = models.CharField(max_length=6)
    description = models.TextField(blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'perfume'


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    perfume = models.ForeignKey(Perfume, models.DO_NOTHING)
    product_type = models.CharField(max_length=11)
    volume_ml = models.DecimalField(max_digits=8, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    is_active = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'product'


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', models.DO_NOTHING)
    product = models.ForeignKey(Product, models.DO_NOTHING)
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    is_verified_purchase = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'review'
        unique_together = (('user', 'product'),)


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'role'


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, models.DO_NOTHING)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField()
    is_active = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'user'
