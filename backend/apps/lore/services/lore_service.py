"""
Lore Service - Main orchestration service for lore operations.

Combines ChromaDB client and chunking for complete lore management.

Based on SYSTEM_DESIGN.md:
- Manages hard canon ingestion
- Manages soft lore from turns
- Provides lore retrieval for prompts
- Handles compaction
"""

import hashlib
import logging
from dataclasses import dataclass, field

from django.db import transaction

from apps.lore.models import LoreChunk
from apps.lore.services.chroma_client import ChromaClientService
from apps.lore.services.chunking import ChunkingService, LoreDeltaChunker
from apps.universes.models import Universe, UniverseHardCanonDoc

logger = logging.getLogger(__name__)


@dataclass
class LoreIngestionResult:
    """Result of lore ingestion operation."""

    success: bool
    document_id: str | None = None
    chunks_created: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class LoreInjectionContext:
    """Context for injecting lore into prompts."""

    hard_canon_chunks: list[dict]
    soft_lore_chunks: list[dict]
    total_tokens_estimate: int
    retrieval_query: str


class LoreService:
    """
    Main service for managing universe lore.

    Provides:
    - Hard canon document ingestion
    - Soft lore delta processing
    - Lore retrieval for prompts
    - Compaction operations

    Usage:
        service = LoreService()
        result = service.ingest_hard_canon(universe, title, text)
        context = service.get_lore_context(universe, query, max_tokens=2000)
    """

    def __init__(self):
        """Initialize lore service."""
        self.chroma = ChromaClientService()
        self.chunker = ChunkingService()
        self.delta_chunker = LoreDeltaChunker()

    def ingest_hard_canon(
        self,
        universe: Universe,
        title: str,
        raw_text: str,
        source_type: str = "upload",
        tags: list[str] | None = None,
        never_compact: bool = True,
    ) -> LoreIngestionResult:
        """
        Ingest a hard canon document.

        Creates:
        1. UniverseHardCanonDoc in Postgres
        2. LoreChunk records in Postgres
        3. Vector embeddings in ChromaDB

        Args:
            universe: The universe to add the document to
            title: Document title
            raw_text: Full document text
            source_type: Type of source (upload, worldgen, user_edit)
            tags: Optional tags for retrieval filtering
            never_compact: If True, document is never compacted

        Returns:
            LoreIngestionResult with operation details
        """
        errors = []
        tags = tags or []

        # Validate input
        if not raw_text or not raw_text.strip():
            return LoreIngestionResult(
                success=False,
                errors=["Document text is empty"],
            )

        try:
            with transaction.atomic():
                # Create checksum for deduplication
                checksum = hashlib.sha256(raw_text.encode()).hexdigest()

                # Check for duplicate
                existing = UniverseHardCanonDoc.objects.filter(
                    universe=universe,
                    checksum=checksum,
                ).first()

                if existing:
                    return LoreIngestionResult(
                        success=False,
                        document_id=str(existing.id),
                        errors=["Document with identical content already exists"],
                    )

                # Create hard canon doc
                doc = UniverseHardCanonDoc.objects.create(
                    universe=universe,
                    source_type=source_type,
                    title=title,
                    raw_text=raw_text,
                    checksum=checksum,
                    never_compact=never_compact,
                )

                # Chunk the document
                chunks = self.chunker.chunk_document(
                    text=raw_text,
                    source_ref=str(doc.id),
                    chunk_type="hard_canon",
                    tags=tags,
                )

                # Create LoreChunk records
                lore_chunks = []
                chroma_docs = []

                for chunk in chunks:
                    lore_chunk = LoreChunk(
                        universe=universe,
                        chunk_type="hard_canon",
                        source_ref=str(doc.id),
                        text=chunk.text,
                        tags_json=chunk.tags,
                        time_range_json=chunk.time_range,
                    )
                    lore_chunks.append(lore_chunk)

                    chroma_docs.append({
                        "id": chunk.id,
                        "text": chunk.text,
                        "chunk_type": "hard_canon",
                        "source_ref": str(doc.id),
                        "tags": chunk.tags,
                        "time_range": chunk.time_range,
                    })

                # Bulk create lore chunks
                LoreChunk.objects.bulk_create(lore_chunks)

                # Add to ChromaDB
                if chroma_docs:
                    try:
                        self.chroma.add_documents_batch(
                            str(universe.id),
                            chroma_docs,
                        )
                    except Exception as e:
                        logger.error(f"ChromaDB ingestion failed: {e}")
                        errors.append(f"Vector embedding failed: {str(e)}")
                        # Don't fail the whole operation - Postgres data is saved

                # Increment universe lore version
                universe.canonical_lore_version += 1
                universe.save(update_fields=["canonical_lore_version"])

                return LoreIngestionResult(
                    success=True,
                    document_id=str(doc.id),
                    chunks_created=len(chunks),
                    errors=errors,
                )

        except Exception as e:
            logger.error(f"Hard canon ingestion failed: {e}")
            return LoreIngestionResult(
                success=False,
                errors=[f"Ingestion failed: {str(e)}"],
            )

    def process_turn_lore_deltas(
        self,
        universe: Universe,
        turn_id: str,
        lore_deltas: list[dict],
    ) -> LoreIngestionResult:
        """
        Process lore deltas from a turn event.

        Args:
            universe: The universe
            turn_id: ID of the turn that generated these deltas
            lore_deltas: List of lore delta dicts from LLM response

        Returns:
            LoreIngestionResult with operation details
        """
        if not lore_deltas:
            return LoreIngestionResult(
                success=True,
                chunks_created=0,
            )

        errors = []

        try:
            with transaction.atomic():
                # Process deltas into chunks
                chunks = self.delta_chunker.process_lore_deltas(
                    lore_deltas,
                    turn_id,
                    campaign_id="",  # TODO: Add campaign context
                )

                if not chunks:
                    return LoreIngestionResult(
                        success=True,
                        chunks_created=0,
                    )

                # Create LoreChunk records
                lore_chunks = []
                chroma_docs = []

                for chunk in chunks:
                    lore_chunk = LoreChunk(
                        universe=universe,
                        chunk_type="soft_lore",
                        source_ref=turn_id,
                        text=chunk.text,
                        tags_json=chunk.tags,
                        time_range_json=chunk.time_range,
                    )
                    lore_chunks.append(lore_chunk)

                    chroma_docs.append({
                        "id": chunk.id,
                        "text": chunk.text,
                        "chunk_type": "soft_lore",
                        "source_ref": turn_id,
                        "tags": chunk.tags,
                        "time_range": chunk.time_range,
                    })

                # Bulk create
                LoreChunk.objects.bulk_create(lore_chunks)

                # Add to ChromaDB
                if chroma_docs:
                    try:
                        self.chroma.add_documents_batch(
                            str(universe.id),
                            chroma_docs,
                        )
                    except Exception as e:
                        logger.error(f"ChromaDB soft lore ingestion failed: {e}")
                        errors.append(f"Vector embedding failed: {str(e)}")

                # Increment lore version
                universe.canonical_lore_version += 1
                universe.save(update_fields=["canonical_lore_version"])

                return LoreIngestionResult(
                    success=True,
                    chunks_created=len(chunks),
                    errors=errors,
                )

        except Exception as e:
            logger.error(f"Soft lore ingestion failed: {e}")
            return LoreIngestionResult(
                success=False,
                errors=[f"Ingestion failed: {str(e)}"],
            )

    def get_lore_context(
        self,
        universe: Universe,
        query: str,
        max_chunks: int = 10,
        include_soft_lore: bool = True,
        prioritize_hard_canon: bool = True,
    ) -> LoreInjectionContext:
        """
        Retrieve relevant lore for prompt injection.

        Args:
            universe: The universe to search
            query: The query text (usually recent game context)
            max_chunks: Maximum number of chunks to return
            include_soft_lore: Include soft lore in results
            prioritize_hard_canon: Give hard canon priority over soft lore

        Returns:
            LoreInjectionContext with relevant chunks
        """
        hard_canon_chunks = []
        soft_lore_chunks = []

        if prioritize_hard_canon:
            # Get hard canon first
            hard_canon_result = self.chroma.query(
                str(universe.id),
                query,
                top_k=max_chunks,
                chunk_type="hard_canon",
            )
            hard_canon_chunks = [
                {
                    "text": r.text,
                    "source": r.source_ref,
                    "score": r.score,
                    "type": "hard_canon",
                }
                for r in hard_canon_result.results
            ]

            # Fill remaining with soft lore if requested
            if include_soft_lore:
                remaining = max_chunks - len(hard_canon_chunks)
                if remaining > 0:
                    soft_result = self.chroma.query(
                        str(universe.id),
                        query,
                        top_k=remaining,
                        chunk_type="soft_lore",
                    )
                    soft_lore_chunks = [
                        {
                            "text": r.text,
                            "source": r.source_ref,
                            "score": r.score,
                            "type": "soft_lore",
                        }
                        for r in soft_result.results
                    ]
        else:
            # Mixed retrieval
            result = self.chroma.query(
                str(universe.id),
                query,
                top_k=max_chunks,
                include_soft_lore=include_soft_lore,
            )

            for r in result.results:
                chunk_data = {
                    "text": r.text,
                    "source": r.source_ref,
                    "score": r.score,
                    "type": r.chunk_type,
                }
                if r.chunk_type == "hard_canon":
                    hard_canon_chunks.append(chunk_data)
                else:
                    soft_lore_chunks.append(chunk_data)

        # Estimate token count (rough approximation: 4 chars per token)
        total_chars = sum(len(c["text"]) for c in hard_canon_chunks + soft_lore_chunks)
        estimated_tokens = total_chars // 4

        return LoreInjectionContext(
            hard_canon_chunks=hard_canon_chunks,
            soft_lore_chunks=soft_lore_chunks,
            total_tokens_estimate=estimated_tokens,
            retrieval_query=query,
        )

    def invalidate_turn_lore(
        self,
        universe: Universe,
        turn_id: str,
    ) -> int:
        """
        Invalidate lore from a specific turn (for rewind).

        Args:
            universe: The universe
            turn_id: ID of the turn to invalidate

        Returns:
            Number of chunks invalidated
        """
        # Delete from Postgres
        deleted_count, _ = LoreChunk.objects.filter(
            universe=universe,
            source_ref=turn_id,
        ).delete()

        # Delete from ChromaDB
        try:
            self.chroma.delete_documents_by_source(
                str(universe.id),
                turn_id,
            )
        except Exception as e:
            logger.error(f"Failed to delete turn lore from ChromaDB: {e}")

        if deleted_count > 0:
            universe.canonical_lore_version += 1
            universe.save(update_fields=["canonical_lore_version"])

        return deleted_count

    def delete_hard_canon_doc(
        self,
        doc: UniverseHardCanonDoc,
    ) -> bool:
        """
        Delete a hard canon document and its chunks.

        Args:
            doc: The document to delete

        Returns:
            True if successful
        """
        try:
            universe = doc.universe
            doc_id = str(doc.id)

            # Delete lore chunks
            LoreChunk.objects.filter(
                universe=universe,
                source_ref=doc_id,
            ).delete()

            # Delete from ChromaDB
            try:
                self.chroma.delete_documents_by_source(
                    str(universe.id),
                    doc_id,
                )
            except Exception as e:
                logger.error(f"Failed to delete from ChromaDB: {e}")

            # Delete the document
            doc.delete()

            # Update lore version
            universe.canonical_lore_version += 1
            universe.save(update_fields=["canonical_lore_version"])

            return True

        except Exception as e:
            logger.error(f"Failed to delete hard canon doc: {e}")
            return False

    def get_universe_lore_stats(self, universe: Universe) -> dict:
        """
        Get statistics about a universe's lore.

        Args:
            universe: The universe

        Returns:
            Dict with lore statistics
        """
        hard_canon_count = LoreChunk.objects.filter(
            universe=universe,
            chunk_type="hard_canon",
        ).count()

        soft_lore_count = LoreChunk.objects.filter(
            universe=universe,
            chunk_type="soft_lore",
        ).count()

        doc_count = UniverseHardCanonDoc.objects.filter(
            universe=universe,
        ).count()

        # Get ChromaDB stats
        chroma_stats = self.chroma.get_collection_stats(str(universe.id))

        return {
            "universe_id": str(universe.id),
            "hard_canon_docs": doc_count,
            "hard_canon_chunks": hard_canon_count,
            "soft_lore_chunks": soft_lore_count,
            "total_chunks": hard_canon_count + soft_lore_count,
            "canonical_lore_version": universe.canonical_lore_version,
            "chroma_stats": chroma_stats,
        }
