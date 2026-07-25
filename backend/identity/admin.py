"""
Django Admin configuration for identity models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission, UserSession, Device


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "tenant", "role", "is_active", "mfa_enabled"]
    list_filter = ["is_active", "is_staff", "mfa_enabled", "tenant", "role"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    filter_horizontal = []  # Override BaseUserAdmin's groups/user_permissions
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Organization", {"fields": ("tenant", "role")}),
        ("Clinical", {"fields": ("license_number", "specialty", "department")}),
        ("Security", {"fields": ("mfa_enabled", "password_reset_required")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important Dates", {"fields": ("last_login", "password_changed_at", "created_at", "updated_at")}),
    )
    readonly_fields = ["created_at", "updated_at"]
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "is_system_role", "created_at"]
    list_filter = ["is_system_role", "tenant"]
    search_fields = ["name"]
    filter_horizontal = ["permissions"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["codename", "resource", "action"]
    list_filter = ["resource"]
    search_fields = ["codename", "description"]
    ordering = ["resource", "action"]


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant", "device_type", "ip_address", "created_at", "expires_at", "is_active"]
    list_filter = ["device_type", "tenant"]
    search_fields = ["user__email", "device_name"]
    readonly_fields = ["created_at", "expires_at"]


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["user", "device_name", "is_trusted", "last_seen_at"]
    list_filter = ["is_trusted"]
    search_fields = ["user__email", "device_name"]
