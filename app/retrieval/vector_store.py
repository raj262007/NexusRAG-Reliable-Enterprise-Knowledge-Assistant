import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4, uuid5, UUID, NAMESPACE_DNS

from qdrant_client import QdrantClient, models

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(
        self,
        storage_path: str = "data/qdrant",
        collection_name: str = "nexusrag"
    ):
        Path(storage_path).mkdir(parents=True, exist_ok=True)
        self.storage_path = str(storage_path)
        self.collection_name = collection_name
        self.client = QdrantClient(path=self.storage_path)

    def create_collection(self, vector_size: int = 384):
        """Create the collection if it does not already exist."""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            logger.info("Created collection %s (dim=%d)", self.collection_name, vector_size)

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        document_id: Optional[str] = None
    ):
        """
        Insert chunks and their corresponding embeddings into Qdrant.
        Preserves metadata and attaches document_id if provided.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings count must match.")

        if not chunks:
            return

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            meta = dict(chunk.get("metadata", {}))
            if document_id and "document_id" not in meta:
                meta["document_id"] = document_id

            # Safe UUID point id
            raw_id = meta.get("chunk_id")
            if not raw_id:
                point_id = str(uuid4())
            else:
                try:
                    UUID(str(raw_id))
                    point_id = str(raw_id)
                except (ValueError, TypeError):
                    point_id = str(uuid5(NAMESPACE_DNS, str(raw_id)))

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "metadata": meta
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(
            "Upserted %d points to collection %s",
            len(points),
            self.collection_name
        )

    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for top-k most similar points.
        Supports document-level filtering via document_id.
        """
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        query_filter = None
        if document_id:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.document_id",
                        match=models.MatchValue(value=document_id)
                    )
                ]
            )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        ).points

        return [
            {
                "id": str(result.id),
                "text": result.payload.get("text", ""),
                "metadata": result.payload.get("metadata", {}),
                "score": float(result.score) if result.score is not None else 0.0
            }
            for result in results
        ]

    def delete_document(self, document_id: str) -> int:
        """
        Delete all points associated with a specific document_id.
        """
        if not document_id:
            return 0

        filt = models.Filter(
            should=[
                models.FieldCondition(
                    key="metadata.document_id",
                    match=models.MatchValue(value=document_id)
                ),
                models.FieldCondition(
                    key="metadata.source",
                    match=models.MatchValue(value=document_id)
                )
            ]
        )

        before_count = self.count()
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=filt)
        )
        after_count = self.count()
        deleted = max(0, before_count - after_count)
        logger.info("Deleted %d points for document %s", deleted, document_id)
        return deleted

    def get_document_chunks(self, document_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve all chunks belonging to a document."""
        filt = models.Filter(
            should=[
                models.FieldCondition(
                    key="metadata.document_id",
                    match=models.MatchValue(value=document_id)
                ),
                models.FieldCondition(
                    key="metadata.source",
                    match=models.MatchValue(value=document_id)
                )
            ]
        )

        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filt,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "id": str(r.id),
                "text": r.payload.get("text", ""),
                "metadata": r.payload.get("metadata", {})
            }
            for r in records
        ]

    def get_all_chunks(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """Retrieve all chunks stored in the collection."""
        if not self.client.collection_exists(self.collection_name):
            return []

        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "id": str(r.id),
                "text": r.payload.get("text", ""),
                "metadata": r.payload.get("metadata", {})
            }
            for r in records
        ]

    def list_documents(self) -> List[Dict[str, Any]]:
        """
        Scan chunks to extract unique documents and their summary metadata.
        """
        all_chunks = self.get_all_chunks(limit=10000)
        docs_map: Dict[str, Dict[str, Any]] = {}

        for ch in all_chunks:
            meta = ch.get("metadata", {})
            doc_id = meta.get("document_id") or meta.get("source") or "unknown"
            source = meta.get("source") or doc_id

            if doc_id not in docs_map:
                docs_map[doc_id] = {
                    "document_id": doc_id,
                    "source": source,
                    "type": meta.get("type", "document"),
                    "total_chunks": 0,
                    "file_path": meta.get("file_path", ""),
                    "uploaded_at": meta.get("uploaded_at", "")
                }
            docs_map[doc_id]["total_chunks"] += 1

        return list(docs_map.values())

    def count(self) -> int:
        """Return the total number of points in the collection."""
        if not self.client.collection_exists(self.collection_name):
            return 0
        res = self.client.count(collection_name=self.collection_name)
        return res.count

    def close(self):
        """Close Qdrant client connection."""
        try:
            self.client.close()
        except Exception:
            pass
