"""
Celery tasks for lore operations.

Includes async tasks for:
- Embedding documents
- Processing turn lore deltas
- Compaction jobs
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def embed_hard_canon_document_task(
    self,
    universe_id: str,
    doc_id: str,
):
    """
    Async task to embed a hard canon document into ChromaDB.

    This is called after a document is uploaded to ensure embedding
    doesn't block the API response.

    Args:
        universe_id: UUID of the universe
        doc_id: UUID of the hard canon document

    Returns:
        Dict with embedding results
    """
    from apps.lore.models import LoreChunk
    from apps.lore.services.chroma_client import ChromaClientService
    from apps.universes.models import UniverseHardCanonDoc

    try:
        doc = UniverseHardCanonDoc.objects.get(id=doc_id)
    except UniverseHardCanonDoc.DoesNotExist:
        return {"success": False, "error": "Document not found"}

    # Get existing chunks for this document
    chunks = LoreChunk.objects.filter(
        universe_id=universe_id,
        source_ref=str(doc_id),
    )

    if not chunks.exists():
        return {
            "success": True,
            "message": "No chunks found to embed",
            "embedded_count": 0,
        }

    # Build documents for ChromaDB
    chroma_docs = []
    for chunk in chunks:
        chroma_docs.append({
            "id": str(chunk.id),
            "text": chunk.text,
            "chunk_type": chunk.chunk_type,
            "source_ref": chunk.source_ref,
            "tags": chunk.tags_json,
            "time_range": chunk.time_range_json,
        })

    # Add to ChromaDB
    try:
        chroma = ChromaClientService()
        chroma.add_documents_batch(universe_id, chroma_docs)
        return {
            "success": True,
            "embedded_count": len(chroma_docs),
            "doc_id": str(doc_id),
        }
    except Exception as e:
        logger.error(f"Failed to embed document {doc_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@shared_task(bind=True)
def process_turn_lore_deltas_task(
    self,
    universe_id: str,
    turn_id: str,
    lore_deltas: list[dict],
):
    """
    Async task to process lore deltas from a turn.

    Args:
        universe_id: UUID of the universe
        turn_id: UUID of the turn event
        lore_deltas: List of lore delta dicts from LLM response

    Returns:
        Dict with processing results
    """
    from apps.lore.services.lore_service import LoreService
    from apps.universes.models import Universe

    try:
        universe = Universe.objects.get(id=universe_id)
    except Universe.DoesNotExist:
        return {"success": False, "error": "Universe not found"}

    service = LoreService()
    result = service.process_turn_lore_deltas(
        universe=universe,
        turn_id=turn_id,
        lore_deltas=lore_deltas,
    )

    return {
        "success": result.success,
        "chunks_created": result.chunks_created,
        "errors": result.errors,
    }


@shared_task(bind=True)
def compact_soft_lore_task(
    self,
    universe_id: str,
    max_chunks_to_compact: int = 100,
    summary_ratio: float = 0.3,
):
    """
    Async task to compact soft lore chunks.

    Compaction reduces storage and improves retrieval by summarizing
    old soft lore chunks into more concise representations.

    Args:
        universe_id: UUID of the universe
        max_chunks_to_compact: Maximum chunks to process in this run
        summary_ratio: Target ratio of compacted to original size

    Returns:
        Dict with compaction results
    """
    from apps.lore.services.compaction import CompactionService
    from apps.universes.models import Universe

    try:
        universe = Universe.objects.get(id=universe_id)
    except Universe.DoesNotExist:
        return {"success": False, "error": "Universe not found"}

    service = CompactionService()
    result = service.compact_soft_lore(
        universe=universe,
        max_chunks=max_chunks_to_compact,
        summary_ratio=summary_ratio,
    )

    return {
        "success": result.success,
        "chunks_compacted": result.chunks_compacted,
        "chunks_removed": result.chunks_removed,
        "errors": result.errors,
    }


@shared_task(bind=True)
def compact_hard_canon_task(
    self,
    universe_id: str,
    doc_id: str,
    force: bool = False,
):
    """
    Async task to compact a hard canon document.

    This is an escape hatch for when hard canon documents become too large.
    Should only be used when explicitly authorized (force=True).

    Args:
        universe_id: UUID of the universe
        doc_id: UUID of the document to compact
        force: Must be True to actually perform compaction

    Returns:
        Dict with compaction results
    """
    from apps.lore.services.compaction import CompactionService
    from apps.universes.models import Universe, UniverseHardCanonDoc

    if not force:
        return {
            "success": False,
            "error": "Hard canon compaction requires force=True",
        }

    try:
        universe = Universe.objects.get(id=universe_id)
        doc = UniverseHardCanonDoc.objects.get(id=doc_id, universe=universe)
    except Universe.DoesNotExist:
        return {"success": False, "error": "Universe not found"}
    except UniverseHardCanonDoc.DoesNotExist:
        return {"success": False, "error": "Document not found"}

    if doc.never_compact:
        return {
            "success": False,
            "error": "Document is marked as never_compact",
        }

    service = CompactionService()
    result = service.compact_hard_canon_doc(doc)

    return {
        "success": result.success,
        "original_chunks": result.original_chunks,
        "compacted_chunks": result.compacted_chunks,
        "errors": result.errors,
    }


@shared_task(bind=True)
def invalidate_turn_lore_task(
    self,
    universe_id: str,
    turn_id: str,
):
    """
    Async task to invalidate lore from a specific turn.

    Used when rewinding gameplay to remove lore that was
    generated after the rewind point.

    Args:
        universe_id: UUID of the universe
        turn_id: UUID of the turn to invalidate

    Returns:
        Dict with invalidation results
    """
    from apps.lore.services.lore_service import LoreService
    from apps.universes.models import Universe

    try:
        universe = Universe.objects.get(id=universe_id)
    except Universe.DoesNotExist:
        return {"success": False, "error": "Universe not found"}

    service = LoreService()
    count = service.invalidate_turn_lore(
        universe=universe,
        turn_id=turn_id,
    )

    return {
        "success": True,
        "chunks_invalidated": count,
    }


@shared_task(bind=True)
def rebuild_universe_embeddings_task(
    self,
    universe_id: str,
):
    """
    Async task to rebuild all embeddings for a universe.

    This clears the ChromaDB collection and re-embeds all lore chunks.
    Useful for recovery or after model changes.

    Args:
        universe_id: UUID of the universe

    Returns:
        Dict with rebuild results
    """
    from apps.lore.models import LoreChunk
    from apps.lore.services.chroma_client import ChromaClientService
    from apps.universes.models import Universe

    try:
        universe = Universe.objects.get(id=universe_id)
    except Universe.DoesNotExist:
        return {"success": False, "error": "Universe not found"}

    chroma = ChromaClientService()

    # Delete existing collection
    chroma.delete_collection(str(universe_id))

    # Get all chunks
    chunks = LoreChunk.objects.filter(universe=universe)

    if not chunks.exists():
        return {
            "success": True,
            "message": "No chunks to embed",
            "embedded_count": 0,
        }

    # Build documents for ChromaDB
    chroma_docs = []
    for chunk in chunks:
        chroma_docs.append({
            "id": str(chunk.id),
            "text": chunk.text,
            "chunk_type": chunk.chunk_type,
            "source_ref": chunk.source_ref,
            "tags": chunk.tags_json,
            "time_range": chunk.time_range_json,
        })

    # Re-embed in batches
    batch_size = 100
    total_embedded = 0

    for i in range(0, len(chroma_docs), batch_size):
        batch = chroma_docs[i:i + batch_size]
        try:
            chroma.add_documents_batch(str(universe_id), batch)
            total_embedded += len(batch)
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            return {
                "success": False,
                "error": str(e),
                "embedded_count": total_embedded,
            }

    return {
        "success": True,
        "embedded_count": total_embedded,
    }
