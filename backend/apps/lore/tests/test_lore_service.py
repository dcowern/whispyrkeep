"""
Tests for lore service.

Tests the LoreService for hard canon ingestion and lore retrieval.
"""

import pytest
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock, patch

from apps.lore.models import LoreChunk
from apps.lore.services.lore_service import LoreService
from apps.universes.models import Universe, UniverseHardCanonDoc

User = get_user_model()


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        username="testuser",
    )


@pytest.fixture
def universe(user):
    """Create test universe."""
    return Universe.objects.create(
        user=user,
        name="Test Universe",
        description="A test universe for lore testing",
    )


@pytest.fixture
def lore_service():
    """Create lore service with mocked ChromaDB."""
    service = LoreService()
    # Mock ChromaDB to avoid needing actual server
    service.chroma = MagicMock()
    service.chroma.add_documents_batch.return_value = []
    service.chroma.query.return_value = MagicMock(results=[])
    return service


@pytest.mark.django_db
class TestHardCanonIngestion:
    """Tests for hard canon document ingestion."""

    def test_ingest_hard_canon_success(self, lore_service, universe):
        """Test successful hard canon ingestion."""
        result = lore_service.ingest_hard_canon(
            universe=universe,
            title="Test Document",
            raw_text="This is a test document with enough content to be chunked properly. " * 10,
            source_type="upload",
            tags=["test", "lore"],
        )

        assert result.success is True
        assert result.document_id is not None
        assert result.chunks_created >= 1

    def test_ingest_creates_document(self, lore_service, universe):
        """Test ingestion creates UniverseHardCanonDoc."""
        lore_service.ingest_hard_canon(
            universe=universe,
            title="My Document",
            raw_text="Document content here." * 20,
        )

        doc = UniverseHardCanonDoc.objects.get(universe=universe, title="My Document")
        assert doc.source_type == "upload"
        assert doc.never_compact is True

    def test_ingest_creates_lore_chunks(self, lore_service, universe):
        """Test ingestion creates LoreChunk records."""
        result = lore_service.ingest_hard_canon(
            universe=universe,
            title="Chunked Document",
            raw_text="This content will be chunked. " * 50,
        )

        doc = UniverseHardCanonDoc.objects.get(id=result.document_id)
        chunks = LoreChunk.objects.filter(
            universe=universe,
            source_ref=str(doc.id),
        )
        assert chunks.count() >= 1
        assert all(c.chunk_type == "hard_canon" for c in chunks)

    def test_ingest_increments_lore_version(self, lore_service, universe):
        """Test ingestion increments universe lore version."""
        original_version = universe.canonical_lore_version

        lore_service.ingest_hard_canon(
            universe=universe,
            title="Version Test",
            raw_text="Content." * 20,
        )

        universe.refresh_from_db()
        assert universe.canonical_lore_version == original_version + 1

    def test_ingest_empty_text_fails(self, lore_service, universe):
        """Test ingestion fails with empty text."""
        result = lore_service.ingest_hard_canon(
            universe=universe,
            title="Empty Document",
            raw_text="",
        )

        assert result.success is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_ingest_duplicate_fails(self, lore_service, universe):
        """Test ingestion fails for duplicate content."""
        text = "Duplicate content here." * 20

        # First upload succeeds
        result1 = lore_service.ingest_hard_canon(
            universe=universe,
            title="First Upload",
            raw_text=text,
        )
        assert result1.success is True

        # Second upload with same content fails
        result2 = lore_service.ingest_hard_canon(
            universe=universe,
            title="Duplicate Upload",
            raw_text=text,
        )
        assert result2.success is False
        assert any("already exists" in e.lower() for e in result2.errors)

    def test_ingest_with_tags(self, lore_service, universe):
        """Test tags are stored in chunks."""
        result = lore_service.ingest_hard_canon(
            universe=universe,
            title="Tagged Document",
            raw_text="Content with tags." * 20,
            tags=["history", "elves"],
        )

        chunks = LoreChunk.objects.filter(source_ref=result.document_id)
        assert all(c.tags_json == ["history", "elves"] for c in chunks)


@pytest.mark.django_db
class TestTurnLoreDeltas:
    """Tests for processing turn lore deltas."""

    def test_process_empty_deltas(self, lore_service, universe):
        """Test processing empty deltas list."""
        result = lore_service.process_turn_lore_deltas(
            universe=universe,
            turn_id="turn123",
            lore_deltas=[],
        )

        assert result.success is True
        assert result.chunks_created == 0

    def test_process_single_delta(self, lore_service, universe):
        """Test processing single lore delta."""
        deltas = [
            {"text": "The party discovered a secret entrance to the dungeon."}
        ]

        result = lore_service.process_turn_lore_deltas(
            universe=universe,
            turn_id="turn123",
            lore_deltas=deltas,
        )

        assert result.success is True
        assert result.chunks_created == 1

        chunk = LoreChunk.objects.get(
            universe=universe,
            source_ref="turn123",
        )
        assert chunk.chunk_type == "soft_lore"

    def test_process_multiple_deltas(self, lore_service, universe):
        """Test processing multiple deltas."""
        deltas = [
            {"text": "First event happened."},
            {"text": "Second event followed."},
            {"text": "Third event concluded."},
        ]

        result = lore_service.process_turn_lore_deltas(
            universe=universe,
            turn_id="turn456",
            lore_deltas=deltas,
        )

        assert result.success is True
        assert result.chunks_created == 3


@pytest.mark.django_db
class TestLoreInvalidation:
    """Tests for lore invalidation (rewind support)."""

    def test_invalidate_turn_lore(self, lore_service, universe):
        """Test invalidating lore from a turn."""
        # First, add some lore
        deltas = [{"text": "Event from this turn."}]
        lore_service.process_turn_lore_deltas(
            universe=universe,
            turn_id="turn_to_rewind",
            lore_deltas=deltas,
        )

        # Verify it exists
        assert LoreChunk.objects.filter(source_ref="turn_to_rewind").exists()

        # Invalidate
        count = lore_service.invalidate_turn_lore(
            universe=universe,
            turn_id="turn_to_rewind",
        )

        assert count == 1
        assert not LoreChunk.objects.filter(source_ref="turn_to_rewind").exists()


@pytest.mark.django_db
class TestLoreStats:
    """Tests for lore statistics."""

    def test_get_universe_lore_stats(self, lore_service, universe):
        """Test getting lore statistics."""
        # Add some content
        lore_service.ingest_hard_canon(
            universe=universe,
            title="Doc 1",
            raw_text="Content." * 20,
        )

        lore_service.process_turn_lore_deltas(
            universe=universe,
            turn_id="turn1",
            lore_deltas=[{"text": "Soft lore content."}],
        )

        stats = lore_service.get_universe_lore_stats(universe)

        assert stats["universe_id"] == str(universe.id)
        assert stats["hard_canon_docs"] == 1
        assert stats["hard_canon_chunks"] >= 1
        assert stats["soft_lore_chunks"] >= 1


@pytest.mark.django_db
class TestDeleteHardCanonDoc:
    """Tests for deleting hard canon documents."""

    def test_delete_hard_canon_doc(self, lore_service, universe):
        """Test deleting a hard canon document."""
        # Create document
        result = lore_service.ingest_hard_canon(
            universe=universe,
            title="To Delete",
            raw_text="Content." * 20,
        )

        doc = UniverseHardCanonDoc.objects.get(id=result.document_id)

        # Delete
        success = lore_service.delete_hard_canon_doc(doc)

        assert success is True
        assert not UniverseHardCanonDoc.objects.filter(id=result.document_id).exists()
        assert not LoreChunk.objects.filter(source_ref=result.document_id).exists()
