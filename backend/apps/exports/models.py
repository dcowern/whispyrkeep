"""
Export job model.

Based on SYSTEM_DESIGN.md section 13.7.
To be fully implemented in Epic 11.
"""

import uuid

from django.conf import settings
from django.db import models


class ExportJob(models.Model):
    """
    Async export job for universe/campaign exports.
    """

    FORMAT_CHOICES = [
        ("json", "JSON"),
        ("md", "Markdown"),
        ("pdf", "PDF"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    EXPORT_TYPE_CHOICES = [
        ("universe", "Universe Export"),
        ("campaign", "Campaign Export"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="export_jobs",
    )
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE_CHOICES)
    target_id = models.UUIDField(help_text="Universe or Campaign ID")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    file_url = models.URLField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Export Job"
        verbose_name_plural = "Export Jobs"

    def __str__(self):
        return f"{self.export_type} ({self.format}) - {self.status}"
