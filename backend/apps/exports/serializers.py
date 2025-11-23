"""
Export serializers.

Provides serialization for export jobs and requests.
"""

from rest_framework import serializers

from apps.exports.models import ExportJob


class ExportJobSerializer(serializers.ModelSerializer):
    """Serializer for export job details."""

    class Meta:
        model = ExportJob
        fields = [
            "id",
            "export_type",
            "target_id",
            "format",
            "status",
            "file_url",
            "error_message",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields


class ExportJobListSerializer(serializers.ModelSerializer):
    """Serializer for export job list view."""

    class Meta:
        model = ExportJob
        fields = [
            "id",
            "export_type",
            "target_id",
            "format",
            "status",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields


class ExportRequestSerializer(serializers.Serializer):
    """Serializer for export request."""

    format = serializers.ChoiceField(
        choices=["json", "md"],
        default="json",
        help_text="Export format: json or md (markdown)",
    )


class ExportResponseSerializer(serializers.Serializer):
    """Serializer for export request response."""

    job_id = serializers.UUIDField()
    status = serializers.CharField()
    message = serializers.CharField()
