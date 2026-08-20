from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0002_alter_ordershippingsnapshot_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnRequest',
            fields=[
                ('return_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('reason', models.CharField(max_length=100)),
                ('details', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[
                    ('Pending', 'Pending'),
                    ('Approved', 'Approved'),
                    ('Rejected', 'Rejected'),
                    ('Received', 'Received'),
                    ('Refunded', 'Refunded'),
                    ('Cancelled', 'Cancelled'),
                ], default='Pending', max_length=10)),
                ('refund_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('admin_note', models.CharField(blank=True, default='', max_length=500)),
                ('requested_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.OneToOneField(db_column='order_id', on_delete=django.db.models.deletion.CASCADE, related_name='return_request', to='accounts.customerorder')),
            ],
            options={
                'db_table': 'return_request',
                'ordering': ['-requested_at'],
            },
        ),
    ]
