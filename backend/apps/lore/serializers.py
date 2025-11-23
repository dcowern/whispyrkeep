"""
Serializers for Lore API.

Handles serialization for lore document upload and retrieval.
"""

from rest_framework import serializers

from apps.lore.models import LoreChunk
from apps.universes.models import Universe, UniverseHardCanonDoc


class HardCanonDocSerializer(serializers.ModelSerializer):
    """Serializer for hard canon documents."""

    universe = serializers.PrimaryKeyRelatedField(
        queryset=Universe.objects.all(),
    )

    class Meta:
        model = UniverseHardCanonDoc
        fields = [
            "id",
            "universe",
            "source_type",
            "title",
            "raw_text",
            "checksum",
            "never_compact",
            "created_at",
        ]
        read_only_fields = ["id", "checksum", "created_at"]


class HardCanonDocListSerializer(serializers.ModelSerializer):
    """Serializer for listing hard canon documents (without full text)."""

    class Meta:
        model = UniverseHardCanonDoc
        fields = [
            "id",
            "universe",
            "source_type",
            "title",
            "never_compact",
            "created_at",
        ]


class HardCanonDocUploadSerializer(serializers.Serializer):
    """Serializer for uploading hard canon documents."""

    title = serializers.CharField(max_length=200)
    raw_text = serializers.CharField()
    source_type = serializers.ChoiceField(
        choices=["upload", "worldgen", "user_edit"],
        default="upload",
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
    )
    never_compact = serializers.BooleanField(default=True)

    def validate_raw_text(self, value):
        """Validate raw text is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Document text cannot be empty")
        if len(value) > 500000:  # 500KB limit
            raise serializers.ValidationError("Document text exceeds maximum size (500KB)")
        return value


class LoreChunkSerializer(serializers.ModelSerializer):
    """Serializer for lore chunks."""

    class Meta:
        model = LoreChunk
        fields = [
            "id",
            "universe",
            "chunk_type",
            "source_ref",
            "text",
            "tags_json",
            "time_range_json",
            "is_compacted",
            "created_at",
        ]
        read_only_fields = fields


class LoreQuerySerializer(serializers.Serializer):
    """Serializer for lore query requests."""

    query = serializers.CharField(max_length=1000)
    max_chunks = serializers.IntegerField(min_value=1, max_value=50, default=10)
    include_soft_lore = serializers.BooleanField(default=True)
    prioritize_hard_canon = serializers.BooleanField(default=True)


class LoreContextSerializer(serializers.Serializer):
    """Serializer for lore context response."""

    hard_canon_chunks = serializers.ListField(
        child=serializers.DictField(),
    )
    soft_lore_chunks = serializers.ListField(
        child=serializers.DictField(),
    )
    total_tokens_estimate = serializers.IntegerField()
    retrieval_query = serializers.CharField()


class LoreStatsSerializer(serializers.Serializer):
    """Serializer for lore statistics."""

    universe_id = serializers.UUIDField()
    hard_canon_docs = serializers.IntegerField()
    hard_canon_chunks = serializers.IntegerField()
    soft_lore_chunks = serializers.IntegerField()
    total_chunks = serializers.IntegerField()
    canonical_lore_version = serializers.IntegerField()
    chroma_stats = serializers.DictField()


class LoreIngestionResultSerializer(serializers.Serializer):
    """Serializer for lore ingestion result."""

    success = serializers.BooleanField()
    document_id = serializers.UUIDField(allow_null=True)
    chunks_created = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())
