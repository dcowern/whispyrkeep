"""
ChromaDB Client Service.

Provides a wrapper around ChromaDB for per-universe lore storage and retrieval.

Based on SYSTEM_DESIGN.md:
- Per-universe vector collections
- Hard canon vs soft lore separation
- Supports both embedding and querying
"""

import hashlib
import logging
from dataclasses import dataclass, field

import chromadb
from chromadb.config import Settings as ChromaSettings
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class LoreSearchResult:
    """Result from a lore search query."""

    chunk_id: str
    text: str
    chunk_type: str  # hard_canon or soft_lore
    source_ref: str
    score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class LoreQueryResult:
    """Results from a lore query."""

    results: list[LoreSearchResult]
    query_text: str
    total_results: int


class ChromaClientService:
    """
    Service for interacting with ChromaDB.

    Manages per-universe collections for lore storage and retrieval.

    Usage:
        service = ChromaClientService()
        service.add_document(universe_id, document_id, text, chunk_type="hard_canon")
        results = service.query(universe_id, "What is the history of...", top_k=5)
    """

    def __init__(self, chroma_url: str | None = None):
        """
        Initialize ChromaDB client.

        Args:
            chroma_url: Optional URL override for ChromaDB server
        """
        self.chroma_url = chroma_url or getattr(settings, "CHROMA_URL", "http://localhost:8001")
        self._client = None

    @property
    def client(self) -> chromadb.HttpClient:
        """Get or create ChromaDB client (lazy initialization)."""
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=self.chroma_url.replace("http://", "").replace("https://", "").split(":")[0],
                port=int(self.chroma_url.split(":")[-1]),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                ),
            )
        return self._client

    def _get_collection_name(self, universe_id: str) -> str:
        """
        Get collection name for a universe.

        Args:
            universe_id: UUID of the universe

        Returns:
            Collection name string
        """
        # ChromaDB collection names must be 3-63 characters, alphanumeric with underscores
        # Use a hash to ensure consistent naming
        hash_suffix = hashlib.md5(str(universe_id).encode()).hexdigest()[:12]
        return f"universe_{hash_suffix}"

    def get_or_create_collection(self, universe_id: str) -> chromadb.Collection:
        """
        Get or create a collection for a universe.

        Args:
            universe_id: UUID of the universe

        Returns:
            ChromaDB collection
        """
        collection_name = self._get_collection_name(universe_id)
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"universe_id": str(universe_id)},
        )

    def add_document(
        self,
        universe_id: str,
        document_id: str,
        text: str,
        chunk_type: str = "hard_canon",
        source_ref: str | None = None,
        tags: list[str] | None = None,
        time_range: dict | None = None,
    ) -> str:
        """
        Add a document/chunk to the universe collection.

        Args:
            universe_id: UUID of the universe
            document_id: Unique ID for this document/chunk
            text: The text content to embed
            chunk_type: Type of lore (hard_canon or soft_lore)
            source_ref: Reference to source (doc ID or turn ID)
            tags: Optional list of tags for filtering
            time_range: Optional time range dict (start_year, end_year)

        Returns:
            The document ID
        """
        collection = self.get_or_create_collection(universe_id)

        metadata = {
            "chunk_type": chunk_type,
            "source_ref": source_ref or document_id,
        }

        if tags:
            metadata["tags"] = ",".join(tags)

        if time_range:
            if "start_year" in time_range:
                metadata["start_year"] = time_range["start_year"]
            if "end_year" in time_range:
                metadata["end_year"] = time_range["end_year"]

        collection.add(
            ids=[str(document_id)],
            documents=[text],
            metadatas=[metadata],
        )

        logger.info(f"Added document {document_id} to universe {universe_id}")
        return str(document_id)

    def add_documents_batch(
        self,
        universe_id: str,
        documents: list[dict],
    ) -> list[str]:
        """
        Add multiple documents/chunks in a batch.

        Args:
            universe_id: UUID of the universe
            documents: List of dicts with keys: id, text, chunk_type, source_ref, tags, time_range

        Returns:
            List of document IDs
        """
        if not documents:
            return []

        collection = self.get_or_create_collection(universe_id)

        ids = []
        texts = []
        metadatas = []

        for doc in documents:
            doc_id = str(doc["id"])
            ids.append(doc_id)
            texts.append(doc["text"])

            metadata = {
                "chunk_type": doc.get("chunk_type", "hard_canon"),
                "source_ref": doc.get("source_ref", doc_id),
            }

            if doc.get("tags"):
                metadata["tags"] = ",".join(doc["tags"])

            if doc.get("time_range"):
                time_range = doc["time_range"]
                if "start_year" in time_range:
                    metadata["start_year"] = time_range["start_year"]
                if "end_year" in time_range:
                    metadata["end_year"] = time_range["end_year"]

            metadatas.append(metadata)

        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(documents)} documents to universe {universe_id}")
        return ids

    def query(
        self,
        universe_id: str,
        query_text: str,
        top_k: int = 5,
        chunk_type: str | None = None,
        include_soft_lore: bool = True,
    ) -> LoreQueryResult:
        """
        Query the universe collection for relevant lore.

        Args:
            universe_id: UUID of the universe
            query_text: The query text to search for
            top_k: Maximum number of results to return
            chunk_type: Optional filter for chunk type (hard_canon or soft_lore)
            include_soft_lore: If False, only return hard_canon chunks

        Returns:
            LoreQueryResult with matching chunks
        """
        collection = self.get_or_create_collection(universe_id)

        # Build where filter
        where_filter = None
        if chunk_type:
            where_filter = {"chunk_type": chunk_type}
        elif not include_soft_lore:
            where_filter = {"chunk_type": "hard_canon"}

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filter,
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return LoreQueryResult(
                results=[],
                query_text=query_text,
                total_results=0,
            )

        # Parse results
        search_results = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results.get("distances") else []

            for i, doc_id in enumerate(ids):
                metadata = metadatas[i] if i < len(metadatas) else {}
                # Convert distance to similarity score (ChromaDB returns L2 distance)
                # Lower distance = higher similarity
                distance = distances[i] if i < len(distances) else 0
                score = 1.0 / (1.0 + distance)  # Convert to 0-1 similarity

                search_results.append(
                    LoreSearchResult(
                        chunk_id=doc_id,
                        text=documents[i] if i < len(documents) else "",
                        chunk_type=metadata.get("chunk_type", "unknown"),
                        source_ref=metadata.get("source_ref", ""),
                        score=score,
                        metadata=metadata,
                    )
                )

        return LoreQueryResult(
            results=search_results,
            query_text=query_text,
            total_results=len(search_results),
        )

    def delete_document(self, universe_id: str, document_id: str) -> bool:
        """
        Delete a document from the collection.

        Args:
            universe_id: UUID of the universe
            document_id: ID of the document to delete

        Returns:
            True if deleted successfully
        """
        try:
            collection = self.get_or_create_collection(universe_id)
            collection.delete(ids=[str(document_id)])
            logger.info(f"Deleted document {document_id} from universe {universe_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    def delete_documents_by_source(self, universe_id: str, source_ref: str) -> int:
        """
        Delete all documents with a given source reference.

        Args:
            universe_id: UUID of the universe
            source_ref: Source reference to match

        Returns:
            Number of documents deleted
        """
        try:
            collection = self.get_or_create_collection(universe_id)

            # First, find documents with this source_ref
            results = collection.get(
                where={"source_ref": source_ref},
            )

            if results and results["ids"]:
                collection.delete(ids=results["ids"])
                count = len(results["ids"])
                logger.info(
                    f"Deleted {count} documents with source_ref {source_ref} "
                    f"from universe {universe_id}"
                )
                return count

            return 0
        except Exception as e:
            logger.error(f"Failed to delete documents by source: {e}")
            return 0

    def delete_collection(self, universe_id: str) -> bool:
        """
        Delete the entire collection for a universe.

        Args:
            universe_id: UUID of the universe

        Returns:
            True if deleted successfully
        """
        try:
            collection_name = self._get_collection_name(universe_id)
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection for universe {universe_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False

    def get_collection_stats(self, universe_id: str) -> dict:
        """
        Get statistics for a universe's collection.

        Args:
            universe_id: UUID of the universe

        Returns:
            Dict with collection statistics
        """
        try:
            collection = self.get_or_create_collection(universe_id)
            count = collection.count()

            return {
                "universe_id": str(universe_id),
                "collection_name": self._get_collection_name(universe_id),
                "total_documents": count,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "universe_id": str(universe_id),
                "collection_name": self._get_collection_name(universe_id),
                "total_documents": 0,
                "error": str(e),
            }
