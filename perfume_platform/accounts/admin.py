"""Single canonical Django admin for the existing MySQL schema.

All business tables are unmanaged Django models backed by the existing
MySQL database.  The old project registered duplicate/incompatible model
classes from catalog/cart/orders; this file is now the only place where the
shared business models are registered.
"""
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.files.storage import default_storage
from django.utils.html import format_html
from django.forms.models import BaseInlineFormSet
from django import forms
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action, display
from unfold.contrib.filters.admin import (
    ChoicesDropdownFilter, RangeDateFilter, RangeNumericFilter, RelatedDropdownFilter,
)
from .models import (
    Role, User, Address, AuditLog, LoginAttempt,
    Brand, Perfume, Product, BulkBottle, DecantBatch,
    Cart, CartItem, CustomerOrder, OrderItem, Payment, Invoice,
    Review, Faq, ChatbotLog, PasswordResetToken,
)
from orders.models import OrderStatusHistory


class FullCrudModelAdmin(ModelAdmin):
    """Common admin contract for normal business records.

    The premium Unfold layout stays unchanged, while every normal business
    model explicitly exposes Add/View/Change/Delete.  The explicit Actions
    column below makes Edit and Delete discoverable on every changelist instead
    of forcing an administrator to guess that clicking a row opens the editor.
    """
    save_on_top = True
    save_as = True
    list_per_page = 50

    def has_add_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        if 'admin_actions' not in fields:
            fields.append('admin_actions')
        return tuple(fields)

    def get_list_display_links(self, request, list_display):
        links = super().get_list_display_links(request, list_display)
        if links:
            return tuple(field for field in links if field != 'admin_actions')
        return links

    @display(description='Actions')
    def admin_actions(self, obj):
        opts = obj._meta
        change_url = reverse(
            f'admin:{opts.app_label}_{opts.model_name}_change',
            args=[obj.pk],
        )
        delete_url = reverse(
            f'admin:{opts.app_label}_{opts.model_name}_delete',
            args=[obj.pk],
        )
        return format_html(
            '<div class="flex flex-wrap items-center gap-2">'
            '<a href="{}" title="Edit / Update" '
            'class="inline-flex items-center gap-1 rounded-default border border-primary-300 '
            'dark:border-primary-700 bg-primary-50 dark:bg-primary-950/30 px-3 py-1.5 '
            'text-xs font-medium text-primary-700 dark:text-primary-300 hover:bg-primary-100 '
            'dark:hover:bg-primary-900/40">'
            '<span class="material-symbols-outlined text-sm">edit</span>Edit</a>'
            '<a href="{}" title="Delete" '
            'class="inline-flex items-center gap-1 rounded-default border border-red-300 '
            'dark:border-red-700 bg-red-50 dark:bg-red-950/30 px-3 py-1.5 '
            'text-xs font-medium text-red-700 dark:text-red-300 hover:bg-red-100 '
            'dark:hover:bg-red-900/40">'
            '<span class="material-symbols-outlined text-sm">delete</span>Delete</a>'
            '</div>',
            change_url,
            delete_url,
        )


@admin.register(Role)
class RoleAdmin(FullCrudModelAdmin):
    list_display = ('role_id', 'role_name')
    list_display_links = list_display
    search_fields = ('role_name',)


@admin.register(User)
class UserAdmin(FullCrudModelAdmin):
    list_display = ('user_id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at')
    list_display_links = list_display
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('role', 'is_active', 'created_at')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Account', {'fields': ('email', 'password_hash', 'role', 'is_active')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('System', {'fields': ('created_at',)}),
    )


@admin.register(Brand)
class BrandAdmin(FullCrudModelAdmin):
    list_display = ('brand_id', 'brand_name', 'country_of_origin')
    list_display_links = list_display
    search_fields = ('brand_name', 'country_of_origin')
    fieldsets = (
        ('Brand', {'fields': ('brand_name', 'country_of_origin', 'description')}),
    )


class PerfumeProductInlineFormSet(BaseInlineFormSet):
    """Require at least one sellable Product variant when a new perfume is created.

    The storefront is product-driven: /api/catalog/products/ returns rows from the
    product table, not bare rows from the perfume table.  Previously the Django
    admin allowed a perfume to be saved without a product variant, which made the
    new perfume appear to save successfully but remain invisible on Home/Shop.
    """
    def clean(self):
        super().clean()
        if not self.instance._state.adding:
            return

        has_product = False
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            required_values = (
                form.cleaned_data.get('product_type'),
                form.cleaned_data.get('volume_ml'),
                form.cleaned_data.get('price'),
                form.cleaned_data.get('stock_quantity'),
            )
            if all(value not in (None, '') for value in required_values):
                has_product = True
                break

        if not has_product:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                'Add at least one Storefront Product Variant (volume, price and stock) before saving. '
                'Home and Shop display Product records, not perfume records alone.'
            )


class PerfumeAdminForm(forms.ModelForm):
    """Safe image upload layer for the existing image_url DB column.

    The legacy schema stores an image reference in VARCHAR(500), so we keep that
    schema unchanged and store the actual file under MEDIA_ROOT.
    """
    image_upload = forms.ImageField(
        required=False,
        label='Upload / Replace Image',
        help_text='JPG, JPEG, PNG or WEBP. The file is stored under MEDIA_ROOT and its path is saved in image_url.',
    )
    # The legacy database used very short ENUM/VARCHAR definitions. The admin now
    # accepts normal fragrance terminology such as "Eau de Parfum (EDP)" without
    # changing the visual layout of the existing admin form.
    concentration = forms.CharField(
        max_length=50,
        required=True,
        label='Concentration',
        help_text='Up to 50 characters, e.g. EDP or Eau de Parfum (EDP).',
    )
    recommended_season = forms.CharField(
        max_length=100,
        required=False,
        label='Recommended season',
        help_text='You can enter multiple seasons, e.g. Spring, Summer.',
    )

    class Meta:
        model = Perfume
        fields = '__all__'

    def clean_image_upload(self):
        image = self.cleaned_data.get('image_upload')
        if image and image.size > 5 * 1024 * 1024:
            raise ValidationError('Image must be 5 MB or smaller.')
        return image


class ProductInlineForm(forms.ModelForm):
    # Common perfume/decant sizes. The database stores volume_ml as DECIMAL,
    # so these are presentation choices only; no database schema change is needed.
    VOLUME_CHOICES = (
        ('2', '2 ml'),
        ('3', '3 ml'),
        ('5', '5 ml'),
        ('10', '10 ml'),
        ('15', '15 ml'),
        ('20', '20 ml'),
        ('30', '30 ml'),
        ('50', '50 ml'),
        ('75', '75 ml'),
        ('100', '100 ml'),
        ('125', '125 ml'),
        ('150', '150 ml'),
        ('200', '200 ml'),
    )

    PRODUCT_TYPE_CHOICES = (
        ('decant', 'Decant'),
        ('full_bottle', 'Full Bottle'),
    )

    product_type = forms.ChoiceField(
        choices=PRODUCT_TYPE_CHOICES,
        label='Product Type',
    )
    volume_ml = forms.ChoiceField(
        choices=VOLUME_CHOICES,
        label='Volume',
        help_text='Choose the bottle/decant size you want to sell.',
    )

    class Meta:
        model = Product
        fields = ('product_type', 'volume_ml', 'price', 'stock_quantity', 'is_active')

    def clean_volume_ml(self):
        from decimal import Decimal
        return Decimal(self.cleaned_data['volume_ml'])


class ProductInline(TabularInline):
    model = Product
    form = ProductInlineForm
    verbose_name = 'Storefront Product Variant'
    verbose_name_plural = 'Storefront Product Variants — choose 5 ml, 10 ml, 20 ml, etc.'
    formset = PerfumeProductInlineFormSet
    extra = 4
    fields = ('product_type', 'volume_ml', 'price', 'stock_quantity', 'is_active', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


@admin.register(Perfume)
class PerfumeAdmin(FullCrudModelAdmin):
    form = PerfumeAdminForm
    list_display = ('perfume_id', 'perfume_name', 'brand', 'concentration', 'target_gender', 'created_at', 'storefront_variants')
    list_display_links = list_display
    search_fields = ('perfume_name', 'brand__brand_name')
    list_filter = ('concentration', 'target_gender', 'recommended_season', 'sillage')
    readonly_fields = ('created_at', 'image_preview')
    inlines = [ProductInline]
    fieldsets = (
        ('Basic Information', {
            'description': 'Important: Home and Shop display sellable Product variants. Add at least one variant below with volume, price and stock.',
            'fields': ('perfume_name', 'brand', 'description', 'image_url', 'image_upload', 'image_preview')
        }),
        ('Fragrance Profile', {
            'fields': ('concentration', 'top_notes', 'middle_notes', 'base_notes', 'longevity_hours', 'sillage')
        }),
        ('Audience & Season', {
            'fields': ('target_gender', 'recommended_season')
        }),
        ('System', {'fields': ('created_at',)}),
    )

    @admin.display(description='Storefront variants')
    def storefront_variants(self, obj):
        return obj.product_set.count()

    @admin.display(description='Current Image')
    def image_preview(self, obj):
        if not obj or not obj.image_url:
            return 'No image uploaded'
        url = obj.image_url
        if not url.startswith(('http://', 'https://', '/')):
            url = '/' + url.lstrip('/')
        if url.startswith('/perfumes/'):
            url = '/media' + url
        elif url.startswith('/media') and not url.startswith('/media/'):
            url = '/media/' + url[len('/media'):].lstrip('/')
        return format_html(
            '<img src="{}" alt="{}" style="max-width:180px;max-height:220px;object-fit:contain;border-radius:8px;" />',
            url,
            obj.perfume_name,
        )

    def save_model(self, request, obj, form, change):
        old_url = obj.image_url
        image = form.cleaned_data.get('image_upload')
        super().save_model(request, obj, form, change)
        if image:
            # Keep filenames predictable but collision-safe through default_storage.
            safe_name = f'perfumes/{obj.perfume_id}_{image.name}'
            saved_path = default_storage.save(safe_name, image)
            obj.image_url = default_storage.url(saved_path)
            obj.save(update_fields=['image_url'])
            if old_url and old_url.startswith('/media/'):
                old_path = old_url[len('/media/'):]
                try:
                    if default_storage.exists(old_path):
                        default_storage.delete(old_path)
                except Exception:
                    # File cleanup must never make an otherwise successful DB save fail.
                    pass


@admin.register(Product)
class ProductAdmin(FullCrudModelAdmin):
    actions = ('activate_products', 'deactivate_products', 'mark_out_of_stock', 'safe_delete_products')
    list_display = ('product_id', 'perfume', 'product_type', 'volume_ml', 'price', 'stock_badge', 'active_badge', 'created_at')
    list_display_links = list_display
    search_fields = ('perfume__perfume_name', 'perfume__brand__brand_name')
    list_filter = (("product_type", ChoicesDropdownFilter), ("price", RangeNumericFilter))
    list_filter_submit = True
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Product', {'fields': ('perfume', 'product_type', 'volume_ml')}),
        ('Pricing & Inventory', {'fields': ('price', 'stock_quantity', 'is_active')}),
        ('System', {'fields': ('created_at',)}),
    )

    @admin.action(description='Activate selected products')
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=1)
        self.message_user(request, f'{updated} product(s) activated.', messages.SUCCESS)

    @admin.action(description='Deactivate selected products')
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=0)
        self.message_user(request, f'{updated} product(s) deactivated.', messages.SUCCESS)

    @admin.action(description='Mark selected products out of stock')
    def mark_out_of_stock(self, request, queryset):
        updated = queryset.update(stock_quantity=0)
        self.message_user(request, f'{updated} product(s) marked out of stock.', messages.WARNING)

    @admin.action(description='Delete selected products safely')
    def safe_delete_products(self, request, queryset):
        deleted = 0
        deactivated = 0
        for product in queryset:
            try:
                product.delete()
                deleted += 1
            except IntegrityError:
                product.is_active = 0
                product.save(update_fields=['is_active'])
                deactivated += 1
        if deleted:
            self.message_user(request, f'{deleted} product(s) deleted.', messages.SUCCESS)
        if deactivated:
            self.message_user(
                request,
                f'{deactivated} product(s) could not be physically deleted because they are referenced by existing records; they were deactivated instead.',
                messages.WARNING,
            )

    @display(description="Active", boolean=True, ordering="is_active")
    def active_badge(self, obj):
        return bool(obj.is_active)

    @display(description="Stock", ordering="stock_quantity",
             label={"OK": "success", "Low": "warning", "Out": "danger"})
    def stock_badge(self, obj):
        if obj.stock_quantity <= 0:
            return "Out", obj.stock_quantity
        if obj.stock_quantity < 5:
            return "Low", obj.stock_quantity
        return "OK", obj.stock_quantity


@admin.register(Review)
class ReviewAdmin(FullCrudModelAdmin):
    list_display = ('review_id', 'product', 'user', 'rating', 'is_verified_purchase', 'created_at')
    list_display_links = list_display
    search_fields = ('product__perfume__perfume_name', 'user__email', 'comment')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Address)
class AddressAdmin(FullCrudModelAdmin):
    list_display = ('address_id', 'user', 'address_line1', 'city', 'country', 'is_default')
    list_display_links = list_display
    search_fields = ('user__email', 'address_line1', 'city', 'country')
    list_filter = ('country', 'is_default')


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'added_at')
    readonly_fields = ('added_at',)


@admin.register(Cart)
class CartAdmin(FullCrudModelAdmin):
    list_display = ('cart_id', 'user', 'created_at', 'updated_at', 'items_count')
    list_display_links = list_display
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]

    @admin.display(description='Items')
    def items_count(self, obj):
        return obj.cartitem_set.count()


@admin.register(CartItem)
class CartItemAdmin(FullCrudModelAdmin):
    list_display = ('cart_item_id', 'cart', 'product', 'quantity', 'added_at')
    list_display_links = list_display
    search_fields = ('cart__user__email', 'product__perfume__perfume_name')
    readonly_fields = ('added_at',)


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)
    can_delete = False


class OrderStatusHistoryInline(TabularInline):
    model = OrderStatusHistory
    extra = 0
    fields = ('status', 'note', 'changed_by', 'created_at')
    readonly_fields = ('status', 'note', 'changed_by', 'created_at')
    can_delete = False


@admin.register(CustomerOrder)
class CustomerOrderAdmin(FullCrudModelAdmin):
    list_display = ('order_id', 'user', 'address', 'status_badge', 'total_amount', 'order_date')
    list_display_links = list_display
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'notes')
    list_filter = (("status", ChoicesDropdownFilter), ("order_date", RangeDateFilter))
    list_filter_submit = True
    readonly_fields = ('order_date', 'status', 'total_amount')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    fieldsets = (
        ('Order', {'fields': ('user', 'address', 'status', 'total_amount', 'notes'), 'description': 'Order status is managed through the dedicated Admin Orders panel so valid status transitions, stock restoration, payment, invoice, and status history stay synchronized.'}),
        ('System', {'fields': ('order_date',)}),
    )
    actions_detail = ["confirm_order", "mark_shipped", "mark_delivered", "cancel_order"]

    @display(
        description="Status",
        ordering="status",
        label={
            "Pending": "warning", "Confirmed": "info", "Processing": "info",
            "Shipped": "info", "Delivered": "success", "Cancelled": "danger",
        },
    )
    def status_badge(self, obj):
        return obj.status

    def _advance(self, request, object_id, new_status):
        from orders.services import advance_order_status
        order = self.get_object(request, object_id)
        try:
            advance_order_status(order, new_status, changed_by=None,
                                 note=f"Set to {new_status} from admin")
            messages.success(request, f"Order #{order.order_id} → {new_status}.")
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "."))

    @action(description="Confirm", icon="check", url_path="confirm-order")
    def confirm_order(self, request, object_id):
        return self._advance(request, object_id, "Confirmed")

    @action(description="Mark shipped", icon="local_shipping", url_path="mark-shipped")
    def mark_shipped(self, request, object_id):
        return self._advance(request, object_id, "Shipped")

    @action(description="Mark delivered", icon="task_alt", url_path="mark-delivered")
    def mark_delivered(self, request, object_id):
        return self._advance(request, object_id, "Delivered")

    @action(description="Cancel", icon="cancel", url_path="cancel-order", variant="danger")
    def cancel_order(self, request, object_id):
        return self._advance(request, object_id, "Cancelled")


@admin.register(OrderItem)
class OrderItemAdmin(FullCrudModelAdmin):
    list_display = ('order_item_id', 'order', 'product', 'quantity', 'unit_price', 'subtotal')
    list_display_links = list_display
    search_fields = ('order__user__email', 'product__perfume__perfume_name')
    readonly_fields = ('subtotal',)


@admin.register(Payment)
class PaymentAdmin(FullCrudModelAdmin):
    list_display = ('payment_id', 'order', 'payment_method', 'amount', 'status', 'payment_date')
    list_display_links = list_display
    search_fields = ('order__user__email', 'transaction_id')
    list_filter = ('payment_method', 'status', 'payment_date')
    readonly_fields = ('payment_date',)


@admin.register(Invoice)
class InvoiceAdmin(FullCrudModelAdmin):
    list_display = ('invoice_id', 'invoice_number', 'order', 'total_amount', 'status', 'issued_date')
    list_display_links = list_display
    search_fields = ('invoice_number', 'order__user__email')
    list_filter = ('status', 'issued_date')
    readonly_fields = ('issued_date',)


@admin.register(BulkBottle)
class BulkBottleAdmin(FullCrudModelAdmin):
    list_display = ('bottle_id', 'perfume', 'batch_number', 'purchase_date', 'bottle_size_ml', 'ml_remaining', 'cost_price')
    list_display_links = list_display
    search_fields = ('batch_number', 'perfume__perfume_name', 'supplier_name')
    list_filter = ('purchase_date', 'authenticity_verified')


@admin.register(DecantBatch)
class DecantBatchAdmin(FullCrudModelAdmin):
    list_display = ('decant_batch_id', 'bottle', 'product', 'quantity_created', 'quantity_sold', 'date_created')
    list_display_links = list_display
    search_fields = ('bottle__batch_number', 'product__perfume__perfume_name')
    readonly_fields = ('date_created',)


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    list_display = ('audit_id', 'user', 'action_type', 'table_affected', 'record_id', 'performed_at')
    search_fields = ('user__email', 'action_type', 'table_affected')
    readonly_fields = ('performed_at',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    list_display = ('attempt_id', 'email_used', 'was_successful', 'attempted_at', 'ip_address')
    search_fields = ('email_used', 'ip_address')
    list_filter = ('was_successful', 'attempted_at')
    readonly_fields = ('attempted_at',)


@admin.register(Faq)
class FaqAdmin(FullCrudModelAdmin):
    list_display = ('faq_id', 'category', 'question', 'is_active', 'created_at', 'updated_at')
    list_display_links = list_display
    search_fields = ('category', 'question', 'answer')
    list_filter = ('category', 'is_active')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatbotLog)
class ChatbotLogAdmin(ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    list_display = ('log_id', 'user', 'session_id', 'timestamp')
    search_fields = ('session_id', 'user_message', 'bot_response', 'user__email')
    readonly_fields = ('timestamp',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(ModelAdmin):
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    list_display = ('token_id', 'user', 'expires_at', 'used_at', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)
