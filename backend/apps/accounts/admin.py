"""Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with UUID and settings fields."""

    list_display = ("email", "display_name", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_active", "created_at")
    search_fields = ("email", "display_name", "username")
    ordering = ("-created_at",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("display_name", "settings_json")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Profile", {"fields": ("email", "display_name")}),
    )
