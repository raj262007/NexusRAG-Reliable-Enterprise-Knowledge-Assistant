import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = 60,
    dense_weight: float = 1.0,
    bm25_weight: float = 1.0,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Combines dense and lexical (BM25) search results using Reciprocal Rank Fusion.

    RRF formula for each doc d:
      Score(d) = sum_{m in {dense, bm25}} (weight_m / (k + rank_m(d)))
    where rank_m(d) is 1-based (1 for top result).
    """
    fused_scores: Dict[str, float] = {}
    doc_registry: Dict[str, Dict[str, Any]] = {}

    def get_doc_key(doc: Dict[str, Any]) -> str:
        # Use explicit chunk_id, or composite of source + page/row + chunk_index, or text hash
        meta = doc.get("metadata", {})
        doc_id = meta.get("document_id") or meta.get("source", "")
        chunk_idx = meta.get("chunk_index", "")
        page_or_row = meta.get("page") or meta.get("row") or meta.get("index") or ""
        text_snippet = doc.get("text", "")[:60]
        return f"{doc_id}:{page_or_row}:{chunk_idx}:{text_snippet}"

    # 1. Process dense results
    for rank, item in enumerate(dense_results, start=1):
        key = get_doc_key(item)
        rrf_val = dense_weight / (k + rank)
        fused_scores[key] = fused_scores.get(key, 0.0) + rrf_val

        if key not in doc_registry:
            doc_registry[key] = {
                "id": item.get("id"),
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
                "dense_score": item.get("score", 0.0),
                "dense_rank": rank,
                "bm25_score": None,
                "bm25_rank": None,
            }
        else:
            doc_registry[key]["dense_score"] = item.get("score", 0.0)
            doc_registry[key]["dense_rank"] = rank

    # 2. Process BM25 results
    for rank, item in enumerate(bm25_results, start=1):
        key = get_doc_key(item)
        rrf_val = bm25_weight / (k + rank)
        fused_scores[key] = fused_scores.get(key, 0.0) + rrf_val

        if key not in doc_registry:
            doc_registry[key] = {
                "id": item.get("id"),
                "text": item.get("text", ""),
                "metadata": item.get("metadata", {}),
                "dense_score": None,
                "dense_rank": None,
                "bm25_score": item.get("score", 0.0),
                "bm25_rank": rank,
            }
        else:
            doc_registry[key]["bm25_score"] = item.get("score", 0.0)
            doc_registry[key]["bm25_rank"] = rank

    # 3. Sort by fused RRF score descending
    sorted_keys = sorted(fused_scores.keys(), key=lambda k: fused_scores[k], reverse=True)

    final_results = []
    for key in sorted_keys[:limit]:
        entry = doc_registry[key]
        entry["score"] = round(fused_scores[key], 6)
        final_results.append(entry)

    return final_results


class HybridRetriever:
    """
    Coordinates dense vector retrieval and BM25 lexical retrieval with Reciprocal Rank Fusion.
    """
    def __init__(
        self,
        vector_store,
        bm25_index,
        embedder,
        k: int = 60,
        dense_weight: float = 1.0,
        bm25_weight: float = 1.0
    ):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.embedder = embedder
        self.k = k
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        document_id: Optional[str] = None,
        mode: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks using 'hybrid', 'dense', or 'lexical' (bm25) mode.
        """
        if not query or not query.strip():
            return []

        limit = max(1, limit)
        fetch_limit = limit * 2  # Retrieve candidates for fusion

        # Mode: lexical only
        if mode == "lexical":
            bm25_res = self.bm25_index.search(query, limit=limit, document_id=document_id)
            for r in bm25_res:
                r["bm25_score"] = r["score"]
            return bm25_res

        # Mode: dense only
        if mode == "dense":
            query_vector = self.embedder.embed_text(query)
            dense_res = self.vector_store.search(
                query_vector,
                limit=limit,
                document_id=document_id
            )
            for r in dense_res:
                r["dense_score"] = r["score"]
            return dense_res

        # Mode: hybrid
        query_vector = self.embedder.embed_text(query)
        dense_results = self.vector_store.search(
            query_vector,
            limit=fetch_limit,
            document_id=document_id
        )

        bm25_results = self.bm25_index.search(
            query,
            limit=fetch_limit,
            document_id=document_id
        )

        return reciprocal_rank_fusion(
            dense_results=dense_results,
            bm25_results=bm25_results,
            k=self.k,
            dense_weight=self.dense_weight,
            bm25_weight=self.bm25_weight,
            limit=limit
        )
