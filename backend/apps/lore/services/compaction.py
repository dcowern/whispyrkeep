"""
Lore Compaction Service.

Handles summarization and compaction of lore chunks to reduce storage
and improve retrieval quality.

Based on SYSTEM_DESIGN.md:
- Soft lore is aggressively compactable
- Hard canon is minimally compacted (escape hatch only)
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.lore.models import LoreChunk
from apps.lore.services.chroma_client import ChromaClientService
from apps.universes.models import Universe, UniverseHardCanonDoc

logger = logging.getLogger(__name__)


@dataclass
class CompactionResult:
    """Result of a compaction operation."""

    success: bool
    chunks_compacted: int = 0
    chunks_removed: int = 0
    original_chunks: int = 0
    compacted_chunks: int = 0
    errors: list[str] = field(default_factory=list)


class CompactionService:
    """
    Service for compacting lore chunks.

    Provides:
    - Soft lore compaction (aggressive)
    - Hard canon compaction (escape hatch)
    - LLM-based summarization (placeholder)

    Usage:
        service = CompactionService()
        result = service.compact_soft_lore(universe, max_chunks=100)
    """

    def __init__(self):
        """Initialize compaction service."""
        self.chroma = ChromaClientService()

    def compact_soft_lore(
        self,
        universe: Universe,
        max_chunks: int = 100,
        summary_ratio: float = 0.3,
        min_age_days: int = 7,
    ) -> CompactionResult:
        """
        Compact soft lore chunks for a universe.

        Finds old soft lore chunks and summarizes them into
        more concise representations.

        Args:
            universe: The universe to compact
            max_chunks: Maximum chunks to process
            summary_ratio: Target ratio of compacted to original size
            min_age_days: Only compact chunks older than this

        Returns:
            CompactionResult with operation details
        """
        errors = []

        # Find old, uncompacted soft lore chunks
        cutoff_date = timezone.now() - timedelta(days=min_age_days)
        chunks_to_compact = LoreChunk.objects.filter(
            universe=universe,
            chunk_type="soft_lore",
            is_compacted=False,
            created_at__lt=cutoff_date,
        ).order_by("created_at")[:max_chunks]

        if not chunks_to_compact.exists():
            return CompactionResult(
                success=True,
                chunks_compacted=0,
            )

        try:
            with transaction.atomic():
                compacted_count = 0
                removed_count = 0

                # Group chunks by source_ref for batch processing
                chunks_by_source = {}
                for chunk in chunks_to_compact:
                    if chunk.source_ref not in chunks_by_source:
                        chunks_by_source[chunk.source_ref] = []
                    chunks_by_source[chunk.source_ref].append(chunk)

                for source_ref, source_chunks in chunks_by_source.items():
                    # Summarize the chunks
                    # TODO: Replace with actual LLM summarization
                    summarized_text = self._summarize_chunks(source_chunks, summary_ratio)

                    if summarized_text:
                        # Create a new compacted chunk
                        new_chunk = LoreChunk.objects.create(
                            universe=universe,
                            chunk_type="soft_lore",
                            source_ref=source_ref,
                            text=summarized_text,
                            tags_json=self._merge_tags(source_chunks),
                            time_range_json=self._merge_time_ranges(source_chunks),
                            is_compacted=True,
                        )

                        # Mark old chunks as compacted and link to new chunk
                        for chunk in source_chunks:
                            chunk.is_compacted = True
                            chunk.supersedes_chunk = new_chunk
                            chunk.save()
                            compacted_count += 1

                        # Update ChromaDB
                        try:
                            # Remove old embeddings
                            for chunk in source_chunks:
                                self.chroma.delete_document(
                                    str(universe.id),
                                    str(chunk.id),
                                )

                            # Add new embedding
                            self.chroma.add_document(
                                str(universe.id),
                                str(new_chunk.id),
                                summarized_text,
                                chunk_type="soft_lore",
                                source_ref=source_ref,
                                tags=new_chunk.tags_json,
                                time_range=new_chunk.time_range_json,
                            )
                        except Exception as e:
                            logger.error(f"ChromaDB update failed during compaction: {e}")
                            errors.append(f"Embedding update failed: {str(e)}")
                    else:
                        # If summarization fails, just mark as compacted
                        for chunk in source_chunks:
                            chunk.is_compacted = True
                            chunk.save()
                            compacted_count += 1

                # Update lore version
                universe.canonical_lore_version += 1
                universe.save(update_fields=["canonical_lore_version"])

                return CompactionResult(
                    success=True,
                    chunks_compacted=compacted_count,
                    chunks_removed=removed_count,
                    errors=errors,
                )

        except Exception as e:
            logger.error(f"Soft lore compaction failed: {e}")
            return CompactionResult(
                success=False,
                errors=[f"Compaction failed: {str(e)}"],
            )

    def compact_hard_canon_doc(
        self,
        doc: UniverseHardCanonDoc,
    ) -> CompactionResult:
        """
        Compact a hard canon document.

        This is an escape hatch for when documents are too large.
        Should only be used when explicitly needed.

        Args:
            doc: The document to compact

        Returns:
            CompactionResult with operation details
        """
        if doc.never_compact:
            return CompactionResult(
                success=False,
                errors=["Document is marked as never_compact"],
            )

        universe = doc.universe

        # Get chunks for this document
        chunks = LoreChunk.objects.filter(
            universe=universe,
            source_ref=str(doc.id),
            is_compacted=False,
        )

        if not chunks.exists():
            return CompactionResult(
                success=True,
                original_chunks=0,
                compacted_chunks=0,
            )

        original_count = chunks.count()

        try:
            with transaction.atomic():
                # Combine all chunk texts
                all_text = "\n\n".join([c.text for c in chunks])

                # Summarize
                # TODO: Replace with actual LLM summarization
                summarized_text = self._summarize_text(all_text, ratio=0.5)

                if not summarized_text:
                    return CompactionResult(
                        success=False,
                        errors=["Summarization failed"],
                    )

                # Create new compacted chunk
                new_chunk = LoreChunk.objects.create(
                    universe=universe,
                    chunk_type="hard_canon",
                    source_ref=str(doc.id),
                    text=summarized_text,
                    tags_json=self._merge_tags(list(chunks)),
                    time_range_json=self._merge_time_ranges(list(chunks)),
                    is_compacted=True,
                )

                # Mark old chunks as compacted
                old_chunk_ids = [str(c.id) for c in chunks]
                chunks.update(is_compacted=True)

                # Update ChromaDB
                try:
                    for chunk_id in old_chunk_ids:
                        self.chroma.delete_document(str(universe.id), chunk_id)

                    self.chroma.add_document(
                        str(universe.id),
                        str(new_chunk.id),
                        summarized_text,
                        chunk_type="hard_canon",
                        source_ref=str(doc.id),
                        tags=new_chunk.tags_json,
                        time_range=new_chunk.time_range_json,
                    )
                except Exception as e:
                    logger.error(f"ChromaDB update failed: {e}")

                # Update lore version
                universe.canonical_lore_version += 1
                universe.save(update_fields=["canonical_lore_version"])

                return CompactionResult(
                    success=True,
                    original_chunks=original_count,
                    compacted_chunks=1,
                )

        except Exception as e:
            logger.error(f"Hard canon compaction failed: {e}")
            return CompactionResult(
                success=False,
                errors=[f"Compaction failed: {str(e)}"],
            )

    def _summarize_chunks(
        self,
        chunks: list[LoreChunk],
        ratio: float,
    ) -> str | None:
        """
        Summarize a list of chunks.

        TODO: Implement actual LLM summarization.
        For now, just concatenates and truncates.
        """
        if not chunks:
            return None

        combined = "\n\n".join([c.text for c in chunks])
        return self._summarize_text(combined, ratio)

    def _summarize_text(
        self,
        text: str,
        ratio: float,
    ) -> str | None:
        """
        Summarize text to target ratio.

        TODO: Implement actual LLM summarization.
        For now, just truncates (placeholder).
        """
        if not text:
            return None

        # Placeholder: truncate to ratio
        # In production, this would call an LLM for proper summarization
        target_length = int(len(text) * ratio)
        if target_length < 50:
            target_length = min(50, len(text))

        # Try to break at sentence boundary
        truncated = text[:target_length]
        last_period = truncated.rfind(".")
        if last_period > target_length * 0.8:
            truncated = truncated[:last_period + 1]

        return truncated + " [Compacted]"

    def _merge_tags(self, chunks: list[LoreChunk]) -> list[str]:
        """Merge tags from multiple chunks."""
        all_tags = set()
        for chunk in chunks:
            if chunk.tags_json:
                all_tags.update(chunk.tags_json)
        return list(all_tags)

    def _merge_time_ranges(self, chunks: list[LoreChunk]) -> dict:
        """Merge time ranges from multiple chunks."""
        start_years = []
        end_years = []

        for chunk in chunks:
            if chunk.time_range_json:
                if "start_year" in chunk.time_range_json:
                    start_years.append(chunk.time_range_json["start_year"])
                if "end_year" in chunk.time_range_json:
                    end_years.append(chunk.time_range_json["end_year"])

        result = {}
        if start_years:
            result["start_year"] = min(start_years)
        if end_years:
            result["end_year"] = max(end_years)

        return result
