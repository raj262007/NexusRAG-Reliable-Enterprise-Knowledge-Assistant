import logging
import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    if not text or not isinstance(text, str):
        return []
    return re.findall(r"\w+", text.lower())


class BM25Index:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def build_index(self, chunks: List[Dict[str, Any]]):
        """
        Build or replace the entire BM25 index from a list of chunks.
        """
        self.chunks = list(chunks)
        self.corpus_tokens = [tokenize(c.get("text", "")) for c in self.chunks]
        if self.corpus_tokens and any(self.corpus_tokens):
            self.bm25 = BM25Okapi(self.corpus_tokens)
            logger.info("BM25 index built with %d documents.", len(self.chunks))
        else:
            self.bm25 = None
            logger.info("BM25 index cleared (empty corpus).")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Append chunks and rebuild index.
        """
        if not chunks:
            return
        combined = self.chunks + chunks
        self.build_index(combined)

    def delete_document(self, document_id: str) -> int:
        """
        Remove all chunks for document_id and rebuild index.
        """
        before_len = len(self.chunks)
        remaining = [
            c for c in self.chunks
            if c.get("metadata", {}).get("document_id") != document_id
            and c.get("metadata", {}).get("source") != document_id
        ]
        deleted = before_len - len(remaining)
        if deleted > 0:
            self.build_index(remaining)
            logger.info("Removed %d chunks from BM25 index for document %s.", deleted, document_id)
        return deleted

    def search(
        self,
        query: str,
        limit: int = 5,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lexical search using BM25Okapi.
        """
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        if not self.bm25 or not self.chunks:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)

        # Pair chunks with scores
        scored_chunks = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            meta = chunk.get("metadata", {})

            # Document-level filter
            if document_id:
                chunk_doc_id = meta.get("document_id") or meta.get("source")
                if chunk_doc_id != document_id:
                    continue

            if score > 0.0:
                scored_chunks.append({
                    "id": chunk.get("id") or str(idx),
                    "text": chunk.get("text", ""),
                    "metadata": meta,
                    "score": float(score)
                })

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:limit]

    def count(self) -> int:
        return len(self.chunks)
