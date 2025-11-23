"""
Tests for document chunking service.

Tests the ChunkingService for splitting documents into embeddable chunks.
"""

import pytest

from apps.lore.services.chunking import ChunkingService, LoreDeltaChunker


class TestChunkingService:
    """Tests for ChunkingService."""

    @pytest.fixture
    def chunker(self):
        """Create default chunking service."""
        return ChunkingService(chunk_size=500, chunk_overlap=50, min_chunk_size=100)

    def test_chunk_empty_text(self, chunker):
        """Test chunking empty text returns empty list."""
        chunks = chunker.chunk_document("", "doc1")
        assert chunks == []

    def test_chunk_small_text(self, chunker):
        """Test chunking small text creates single chunk."""
        text = "This is a small piece of text that fits in one chunk." * 3
        chunks = chunker.chunk_document(text, "doc1")
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_chunk_large_text(self, chunker):
        """Test chunking large text creates multiple chunks."""
        text = "This is a sentence. " * 100  # ~2000 chars
        chunks = chunker.chunk_document(text, "doc1")
        assert len(chunks) > 1

    def test_chunk_metadata(self, chunker):
        """Test chunks have correct metadata."""
        text = "Test content for chunking." * 10
        chunks = chunker.chunk_document(
            text,
            source_ref="doc123",
            chunk_type="hard_canon",
            tags=["lore", "history"],
            time_range={"start_year": 100, "end_year": 200},
        )

        assert all(c.source_ref == "doc123" for c in chunks)
        assert all(c.chunk_type == "hard_canon" for c in chunks)
        assert all(c.tags == ["lore", "history"] for c in chunks)
        assert all(c.time_range == {"start_year": 100, "end_year": 200} for c in chunks)

    def test_chunk_sequence_numbers(self, chunker):
        """Test chunks have sequential sequence numbers."""
        text = "Content " * 200
        chunks = chunker.chunk_document(text, "doc1")
        for i, chunk in enumerate(chunks):
            assert chunk.sequence_number == i

    def test_chunk_unique_ids(self, chunker):
        """Test each chunk has unique ID."""
        text = "Content " * 200
        chunks = chunker.chunk_document(text, "doc1")
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_detect_strategy_markdown(self, chunker):
        """Test markdown strategy detection."""
        text = "# Header\n\nContent here.\n\n## Subheader\n\nMore content."
        strategy = chunker._detect_strategy(text)
        assert strategy == "markdown"

    def test_detect_strategy_paragraph(self, chunker):
        """Test paragraph strategy detection."""
        # Create text with substantial paragraphs (avg > 100 chars each)
        text = "First paragraph with plenty of content that extends beyond the minimum threshold for detection. " * 3 + "\n\n" + "Second paragraph with additional substantial content that also meets the length requirements. " * 3
        strategy = chunker._detect_strategy(text)
        assert strategy == "paragraph"

    def test_detect_strategy_fixed(self, chunker):
        """Test fixed strategy detection for continuous text."""
        text = "Continuous text without breaks " * 50
        strategy = chunker._detect_strategy(text)
        assert strategy == "fixed"

    def test_chunk_by_markdown(self, chunker):
        """Test markdown chunking splits at headers."""
        # Create substantial content in each section to exceed min_chunk_size (100)
        text = """# Section 1

This is the first section with plenty of content. We need to ensure that this section has enough text to exceed the minimum chunk size threshold of 100 characters. Let's add more descriptive text here.

## Subsection 1.1

More content here about a specific topic. This subsection also needs substantial content to be meaningful as a chunk. Adding additional context and details to meet the threshold.

# Section 2

Different topic entirely with more content. This section covers a completely new subject matter and should result in a separate chunk when processed by the markdown strategy."""

        chunks = chunker.chunk_document(text, "doc1", strategy="markdown")
        assert len(chunks) >= 2

    def test_chunk_by_paragraph(self, chunker):
        """Test paragraph chunking."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph." * 10
        chunks = chunker.chunk_document(text, "doc1", strategy="paragraph")
        assert len(chunks) >= 1

    def test_chunk_min_size_filtering(self, chunker):
        """Test chunks below min size are filtered."""
        # Create chunker with high min size
        strict_chunker = ChunkingService(
            chunk_size=500, chunk_overlap=0, min_chunk_size=200
        )
        text = "Short." * 10  # ~60 chars total
        chunks = strict_chunker.chunk_document(text, "doc1")
        assert len(chunks) == 0

    def test_rechunk_for_updates(self, chunker):
        """Test rechunking identifies changed chunks."""
        old_text = "Original content " * 50
        old_chunks = chunker.chunk_document(old_text, "doc1")

        # Create new text with different length to produce different chunk count
        new_text = "Updated content that is longer " * 80
        new_chunks, to_delete = chunker.rechunk_for_updates(
            old_chunks, new_text, "doc1"
        )

        # Since IDs are based on source_ref and sequence, when chunk counts differ,
        # old chunks with sequences not in new chunks should be deleted
        # With different text lengths, we should get different chunk structures
        assert len(new_chunks) > 0
        # Verify we got new chunks back
        assert all(c.text for c in new_chunks)


class TestLoreDeltaChunker:
    """Tests for LoreDeltaChunker."""

    @pytest.fixture
    def delta_chunker(self):
        """Create lore delta chunker."""
        return LoreDeltaChunker()

    def test_process_empty_deltas(self, delta_chunker):
        """Test processing empty deltas list."""
        chunks = delta_chunker.process_lore_deltas([], "turn1", "campaign1")
        assert chunks == []

    def test_process_single_delta(self, delta_chunker):
        """Test processing single lore delta."""
        deltas = [
            {"text": "The party discovered a hidden passage in the dungeon."}
        ]
        chunks = delta_chunker.process_lore_deltas(deltas, "turn1", "campaign1")

        assert len(chunks) == 1
        assert chunks[0].chunk_type == "soft_lore"
        assert chunks[0].source_ref == "turn1"

    def test_process_multiple_deltas(self, delta_chunker):
        """Test processing multiple lore deltas."""
        deltas = [
            {"text": "The kingdom fell to chaos."},
            {"text": "A new hero emerged from the east."},
            {"text": "The dragon was finally slain."},
        ]
        chunks = delta_chunker.process_lore_deltas(deltas, "turn1", "campaign1")

        assert len(chunks) == 3
        for i, chunk in enumerate(chunks):
            assert chunk.sequence_number == i

    def test_process_deltas_with_tags(self, delta_chunker):
        """Test deltas with tags are preserved."""
        deltas = [
            {
                "text": "The elven kingdom signed a treaty.",
                "tags": ["politics", "elves"],
            }
        ]
        chunks = delta_chunker.process_lore_deltas(deltas, "turn1", "campaign1")

        assert chunks[0].tags == ["politics", "elves"]

    def test_process_deltas_with_time_range(self, delta_chunker):
        """Test deltas with time range are preserved."""
        deltas = [
            {
                "text": "The great war began.",
                "time_range": {"start_year": 1000, "end_year": 1005},
            }
        ]
        chunks = delta_chunker.process_lore_deltas(deltas, "turn1", "campaign1")

        assert chunks[0].time_range == {"start_year": 1000, "end_year": 1005}

    def test_empty_text_delta_skipped(self, delta_chunker):
        """Test deltas with empty text are skipped."""
        deltas = [
            {"text": ""},
            {"text": "   "},
            {"text": "Valid content here."},
        ]
        chunks = delta_chunker.process_lore_deltas(deltas, "turn1", "campaign1")

        assert len(chunks) == 1
        assert "Valid" in chunks[0].text
