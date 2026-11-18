import pytest
from app.retrieval.bm25_index import BM25Index, tokenize
from app.retrieval.hybrid_search import reciprocal_rank_fusion, HybridRetriever


class FakeEmbedder:
    def __init__(self, dim=3):
        self.dimension = dim

    def embed_text(self, text: str) -> list[float]:
        # Return deterministic vector
        if "python" in text.lower():
            return [1.0, 0.0, 0.0]
        elif "machine" in text.lower() or "ai" in text.lower():
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


def test_bm25_tokenization():
    tokens = tokenize("NexusRAG: Hybrid Search 101!")
    assert tokens == ["nexusrag", "hybrid", "search", "101"]


def test_bm25_index_and_search():
    index = BM25Index()
    chunks = [
        {"id": "c1", "text": "Python is a modern high-level programming language.", "metadata": {"source": "python.txt"}},
        {"id": "c2", "text": "Qdrant is a high performance vector search engine.", "metadata": {"source": "qdrant.txt"}},
        {"id": "c3", "text": "Deep learning models require GPUs or CPUs for inference.", "metadata": {"source": "dl.txt"}}
    ]
    index.build_index(chunks)
    assert index.count() == 3

    results = index.search("python programming", limit=2)
    assert len(results) > 0
    assert results[0]["id"] == "c1"
    assert results[0]["score"] > 0

    # Delete doc
    deleted = index.delete_document("python.txt")
    assert deleted == 1
    assert index.count() == 2
    empty_res = index.search("python programming", limit=2)
    assert len(empty_res) == 0


def test_reciprocal_rank_fusion():
    dense_results = [
        {"id": "c1", "text": "First doc", "metadata": {"source": "a.pdf"}, "score": 0.95},
        {"id": "c2", "text": "Second doc", "metadata": {"source": "b.pdf"}, "score": 0.85},
    ]
    bm25_results = [
        {"id": "c2", "text": "Second doc", "metadata": {"source": "b.pdf"}, "score": 2.5},
        {"id": "c3", "text": "Third doc", "metadata": {"source": "c.pdf"}, "score": 1.5},
    ]

    fused = reciprocal_rank_fusion(
        dense_results=dense_results,
        bm25_results=bm25_results,
        k=60,
        limit=3
    )

    assert len(fused) == 3
    # c2 is present in both lists (rank 2 in dense, rank 1 in bm25)
    # c1 is rank 1 in dense (1/61 = 0.01639)
    # c2 is rank 2 in dense + rank 1 in bm25 (1/62 + 1/61 = 0.016129 + 0.016393 = 0.0325) -> c2 should be #1!
    assert fused[0]["text"] == "Second doc"
    assert fused[0]["dense_score"] == 0.85
    assert fused[0]["bm25_score"] == 2.5
    assert fused[0]["score"] > fused[1]["score"]
