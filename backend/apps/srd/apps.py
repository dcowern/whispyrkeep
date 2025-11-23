"""SRD app configuration."""

from django.apps import AppConfig


class SrdConfig(AppConfig):
    """Configuration for the SRD catalog app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.srd"
    verbose_name = "SRD 5.2 Catalog"
