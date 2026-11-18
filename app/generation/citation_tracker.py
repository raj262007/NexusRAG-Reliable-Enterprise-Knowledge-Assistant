from typing import List, Dict, Any


def extract_citations(retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format and structure verified citations from retrieved evidence chunks.
    Ensures citations reflect actual retrieved evidence without fabrication.
    """
    citations = []

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        meta = chunk.get("metadata", {})
        source = meta.get("source") or meta.get("file_name", "Unknown Document")
        page = meta.get("page")
        row = meta.get("row")
        chunk_idx = meta.get("chunk_index", 0)
        score = chunk.get("score", 0.0)
        text = chunk.get("text", "").strip()

        # Build human-readable location tag
        location_parts = []
        if page is not None:
            location_parts.append(f"Page {page}")
        if row is not None:
            location_parts.append(f"Row {row}")
        if chunk_idx is not None:
            location_parts.append(f"Chunk {chunk_idx}")

        loc_label = f" ({', '.join(location_parts)})" if location_parts else ""

        # Create 180-char clean snippet preview
        snippet = text[:200] + "..." if len(text) > 200 else text

        citations.append({
            "id": idx,
            "source": source,
            "page": page,
            "row": row,
            "chunk_index": chunk_idx,
            "location_label": loc_label.strip(),
            "score": round(score, 4),
            "dense_score": round(chunk.get("dense_score"), 4) if chunk.get("dense_score") is not None else None,
            "bm25_score": round(chunk.get("bm25_score"), 4) if chunk.get("bm25_score") is not None else None,
            "text": text,
            "snippet": snippet,
            "document_id": meta.get("document_id")
        })

    return citations
