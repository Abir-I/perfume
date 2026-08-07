"""
Accounts Admin Interface
"""

from django.contrib import admin
from .models import Address, Role, User, AuditLog, LoginAttempt


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role admin"""
    list_display = ('role_name',)
    search_fields = ('role_name',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User admin"""
    list_display = ('user_id', 'email', 'first_name', 'last_name', 'role')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('role', 'created_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('email', 'password_hash')
        }),
        ('Personal', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender')
        }),
        ('Account', {
            'fields': ('role', 'is_active', 'created_at')
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Address admin"""
    list_display = ('address_id', 'user', 'city', 'country', 'is_default')
    search_fields = ('user__email', 'city', 'country')
    list_filter = ('country', 'is_default')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit log admin"""
    list_display = ('audit_id', 'user', 'action_type', 'table_affected', 'performed_at')
    search_fields = ('user__email', 'action_type', 'table_affected')
    list_filter = ('action_type', 'table_affected', 'performed_at')
    readonly_fields = ('performed_at',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Login attempt admin"""
    list_display = ('attempt_id', 'email_used', 'was_successful', 'attempted_at')
    search_fields = ('email_used',)
    list_filter = ('was_successful', 'attempted_at')
    readonly_fields = ('attempted_at',)
