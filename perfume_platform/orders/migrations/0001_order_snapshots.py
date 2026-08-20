from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [('accounts', '0002_schema_defaults')]

    operations = [
        migrations.CreateModel(
            name='OrderShippingSnapshot',
            fields=[
                ('snapshot_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=255)),
                ('phone', models.CharField(max_length=20)),
                ('address_line1', models.CharField(max_length=255)),
                ('address_line2', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(default='Bangladesh', max_length=100)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order', models.OneToOneField(db_column='order_id', on_delete=django.db.models.deletion.CASCADE, related_name='shipping_snapshot', to='accounts.customerorder')),
            ],
            options={'db_table': 'order_shipping_snapshot'},
        ),
        migrations.CreateModel(
            name='OrderFinancialSnapshot',
            fields=[
                ('snapshot_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('shipping_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order', models.OneToOneField(db_column='order_id', on_delete=django.db.models.deletion.CASCADE, related_name='financial_snapshot', to='accounts.customerorder')),
            ],
            options={'db_table': 'order_financial_snapshot'},
        ),
        migrations.CreateModel(
            name='OrderItemSnapshot',
            fields=[
                ('snapshot_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('product_name', models.CharField(max_length=200)),
                ('brand_name', models.CharField(blank=True, max_length=150)),
                ('product_type', models.CharField(max_length=30)),
                ('volume_ml', models.DecimalField(decimal_places=2, max_digits=8)),
                ('quantity', models.IntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=12)),
                ('image_url', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order_item', models.OneToOneField(db_column='order_item_id', on_delete=django.db.models.deletion.CASCADE, related_name='purchase_snapshot', to='accounts.orderitem')),
            ],
            options={'db_table': 'order_item_snapshot'},
        ),
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('history_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(max_length=10)),
                ('note', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('changed_by', models.ForeignKey(blank=True, db_column='changed_by', null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
                ('order', models.ForeignKey(db_column='order_id', on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='accounts.customerorder')),
            ],
            options={'db_table': 'order_status_history', 'ordering': ['created_at', 'history_id']},
        ),
    ]
