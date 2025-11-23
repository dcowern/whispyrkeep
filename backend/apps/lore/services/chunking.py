"""
Document Chunking Service.

Handles splitting documents into chunks suitable for embedding.

Based on SYSTEM_DESIGN.md:
- Hard canon documents need to be chunked for vector search
- Soft lore deltas from turns should be chunked as well
"""

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TextChunk:
    """A chunk of text ready for embedding."""

    id: str
    text: str
    chunk_type: str  # hard_canon or soft_lore
    source_ref: str
    tags: list[str] = field(default_factory=list)
    time_range: dict = field(default_factory=dict)
    sequence_number: int = 0  # Order within the source document


class ChunkingService:
    """
    Service for chunking text documents into smaller pieces.

    Supports multiple chunking strategies:
    - Fixed size (with overlap)
    - Paragraph-based
    - Section-based (markdown headers)

    Usage:
        service = ChunkingService(chunk_size=500, chunk_overlap=50)
        chunks = service.chunk_document(text, "doc_id", chunk_type="hard_canon")
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Target size for chunks (in characters)
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size (discard smaller)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_document(
        self,
        text: str,
        source_ref: str,
        chunk_type: str = "hard_canon",
        tags: Optional[list[str]] = None,
        time_range: Optional[dict] = None,
        strategy: str = "auto",
    ) -> list[TextChunk]:
        """
        Chunk a document into smaller pieces.

        Args:
            text: The full text to chunk
            source_ref: Reference to the source document
            chunk_type: Type of lore (hard_canon or soft_lore)
            tags: Optional tags to apply to all chunks
            time_range: Optional time range for all chunks
            strategy: Chunking strategy (auto, fixed, paragraph, markdown)

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        tags = tags or []
        time_range = time_range or {}

        # Choose strategy
        if strategy == "auto":
            strategy = self._detect_strategy(text)

        # Apply strategy
        if strategy == "markdown":
            raw_chunks = self._chunk_by_markdown(text)
        elif strategy == "paragraph":
            raw_chunks = self._chunk_by_paragraph(text)
        else:
            raw_chunks = self._chunk_fixed_size(text)

        # Create TextChunk objects
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                continue

            chunk_id = self._generate_chunk_id(source_ref, i)
            chunks.append(
                TextChunk(
                    id=chunk_id,
                    text=chunk_text.strip(),
                    chunk_type=chunk_type,
                    source_ref=source_ref,
                    tags=tags.copy(),
                    time_range=time_range.copy(),
                    sequence_number=i,
                )
            )

        return chunks

    def _detect_strategy(self, text: str) -> str:
        """
        Detect the best chunking strategy for text.

        Args:
            text: The text to analyze

        Returns:
            Strategy name (markdown, paragraph, or fixed)
        """
        # Check for markdown headers
        markdown_pattern = r"^#{1,6}\s+"
        if re.search(markdown_pattern, text, re.MULTILINE):
            return "markdown"

        # Check for clear paragraph breaks
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            avg_para_len = sum(len(p) for p in paragraphs) / len(paragraphs)
            if avg_para_len > 100:  # Substantial paragraphs
                return "paragraph"

        return "fixed"

    def _chunk_fixed_size(self, text: str) -> list[str]:
        """
        Chunk text using fixed size windows with overlap.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary (., !, ?) within the last 20% of the chunk
                search_start = int(start + self.chunk_size * 0.8)
                sentence_break = -1

                for punct in [".", "!", "?", "\n"]:
                    pos = text.rfind(punct, search_start, end)
                    if pos > sentence_break:
                        sentence_break = pos

                if sentence_break > start:
                    end = sentence_break + 1
                else:
                    # Fall back to word boundary
                    space_pos = text.rfind(" ", search_start, end)
                    if space_pos > start:
                        end = space_pos

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap
            if start <= 0 or start >= len(text):
                break

        return chunks

    def _chunk_by_paragraph(self, text: str) -> list[str]:
        """
        Chunk text by paragraphs, merging small ones.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            # If adding this paragraph would exceed chunk size, finalize current chunk
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(para)
            current_size += para_size

        # Add remaining content
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _chunk_by_markdown(self, text: str) -> list[str]:
        """
        Chunk text by markdown sections.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Split by headers while keeping the headers
        header_pattern = r"(^#{1,6}\s+[^\n]+$)"
        parts = re.split(header_pattern, text, flags=re.MULTILINE)

        chunks = []
        current_chunk = []
        current_size = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            is_header = re.match(r"^#{1,6}\s+", part)
            part_size = len(part)

            # If this is a header and we have content, consider finalizing
            if is_header and current_size > self.min_chunk_size:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            # If adding this part would exceed chunk size significantly
            if current_size + part_size > self.chunk_size * 1.5 and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(part)
            current_size += part_size

        # Add remaining content
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _generate_chunk_id(self, source_ref: str, sequence: int) -> str:
        """
        Generate a unique ID for a chunk.

        Args:
            source_ref: Reference to the source document
            sequence: Sequence number within the document

        Returns:
            Unique chunk ID
        """
        # Create a deterministic ID based on source and sequence
        hash_input = f"{source_ref}:{sequence}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"chunk_{hash_suffix}_{sequence}"

    def rechunk_for_updates(
        self,
        old_chunks: list[TextChunk],
        new_text: str,
        source_ref: str,
        chunk_type: str = "hard_canon",
        tags: Optional[list[str]] = None,
        time_range: Optional[dict] = None,
    ) -> tuple[list[TextChunk], list[str]]:
        """
        Re-chunk a document and determine which chunks changed.

        Useful for incremental updates to documents.

        Args:
            old_chunks: Previous chunks from this document
            new_text: New full text of the document
            source_ref: Reference to the source document
            chunk_type: Type of lore
            tags: Optional tags
            time_range: Optional time range

        Returns:
            Tuple of (new chunks, IDs of chunks to delete)
        """
        # Generate new chunks
        new_chunks = self.chunk_document(
            new_text,
            source_ref,
            chunk_type=chunk_type,
            tags=tags,
            time_range=time_range,
        )

        # Find old chunk IDs to delete
        old_ids = {chunk.id for chunk in old_chunks}
        new_ids = {chunk.id for chunk in new_chunks}

        # All old chunks should be deleted since IDs are deterministic
        # Any old chunk not in new set should be removed
        chunks_to_delete = list(old_ids - new_ids)

        return new_chunks, chunks_to_delete


class LoreDeltaChunker:
    """
    Specialized chunker for turn-based lore deltas.

    Handles the lore_deltas array from turn events.
    """

    def __init__(self):
        """Initialize lore delta chunker."""
        self.base_chunker = ChunkingService(
            chunk_size=300,  # Smaller chunks for deltas
            chunk_overlap=0,  # No overlap needed
            min_chunk_size=50,
        )

    def process_lore_deltas(
        self,
        lore_deltas: list[dict],
        turn_id: str,
        campaign_id: str,
    ) -> list[TextChunk]:
        """
        Process lore deltas from a turn event.

        Args:
            lore_deltas: List of lore delta dicts from LLM
                Each delta should have: text, tags (optional), time_range (optional)
            turn_id: ID of the turn that generated these deltas
            campaign_id: ID of the campaign

        Returns:
            List of TextChunk objects ready for embedding
        """
        chunks = []

        for i, delta in enumerate(lore_deltas):
            text = delta.get("text", "").strip()
            if not text:
                continue

            chunk_id = f"delta_{turn_id}_{i}"

            chunks.append(
                TextChunk(
                    id=chunk_id,
                    text=text,
                    chunk_type="soft_lore",
                    source_ref=turn_id,
                    tags=delta.get("tags", []),
                    time_range=delta.get("time_range", {}),
                    sequence_number=i,
                )
            )

        return chunks
