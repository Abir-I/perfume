from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]

    operations = [
        migrations.AlterField(model_name='address', name='country', field=models.CharField(default='Bangladesh', max_length=100)),
        migrations.AlterField(model_name='address', name='is_default', field=models.IntegerField(default=0)),
        migrations.AlterField(model_name='cart', name='created_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='cart', name='updated_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='cartitem', name='quantity', field=models.IntegerField(default=1)),
        migrations.AlterField(model_name='customerorder', name='order_date', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='customerorder', name='status', field=models.CharField(default='Pending', max_length=10)),
        migrations.AlterField(model_name='decantbatch', name='date_created', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='faq', name='created_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='faq', name='updated_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='faq', name='is_active', field=models.IntegerField(default=1)),
        migrations.AlterField(model_name='invoice', name='issued_date', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='invoice', name='tax_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AlterField(model_name='invoice', name='status', field=models.CharField(default='Issued', max_length=9)),
        migrations.AlterField(model_name='passwordresettoken', name='created_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='payment', name='payment_date', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='payment', name='status', field=models.CharField(default='Pending', max_length=9)),
        migrations.AlterField(model_name='perfume', name='created_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='product', name='stock_quantity', field=models.IntegerField(default=0)),
        migrations.AlterField(model_name='product', name='is_active', field=models.IntegerField(default=1)),
        migrations.AlterField(model_name='product', name='created_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='review', name='created_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='review', name='is_verified_purchase', field=models.IntegerField(default=0)),
        migrations.AlterField(model_name='user', name='created_at', field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AlterField(model_name='user', name='is_active', field=models.IntegerField(default=1)),
    ]
