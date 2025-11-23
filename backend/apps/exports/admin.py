"""Admin configuration for exports app."""

from django.contrib import admin

from apps.exports.models import ExportJob


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    """Admin for export jobs."""

    list_display = ("export_type", "format", "user", "status", "created_at")
    list_filter = ("export_type", "format", "status", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("id", "created_at", "completed_at")
