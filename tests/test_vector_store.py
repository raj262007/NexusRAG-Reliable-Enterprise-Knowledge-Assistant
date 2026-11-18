import pytest
from app.retrieval.vector_store import VectorStore

def test_vector_store_insert_and_search(tmp_path):
    store = VectorStore(
        storage_path=str(tmp_path / "qdrant_test"),
        collection_name="test_collection"
    )
    try:
        store.create_collection(vector_size=3)
        chunks = [
            {
                "text": "Python is a programming language.",
                "metadata": {"source": "python.pdf", "page": 1}
            },
            {
                "text": "Machine learning uses data to learn patterns.",
                "metadata": {"source": "ml.pdf", "page": 2}
            }
        ]
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
        store.add_chunks(chunks, embeddings)
        results = store.search(
            query_embedding=[1.0, 0.0, 0.0],
            limit=2
        )
        assert len(results) == 2
        assert results[0]["text"] == "Python is a programming language."
        assert results[0]["metadata"]["source"] == "python.pdf"
        assert results[0]["score"] > results[1]["score"]
    finally:
        store.close()
def test_mismatched_embeddings(tmp_path):
    store = VectorStore(
        storage_path=str(tmp_path / "qdrant_test"),
        collection_name="test_collection"
    )

    try:
        store.create_collection(vector_size=3)

        chunks = [{"text": "Hello", "metadata": {}}]
        embeddings = []

        with pytest.raises(ValueError):
            store.add_chunks(chunks, embeddings)

    finally:
        store.close()
