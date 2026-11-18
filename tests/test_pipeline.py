import pytest
from pathlib import Path
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.vector_store import VectorStore
from app.retrieval.bm25_index import BM25Index


class DummyEmbedder:
    def __init__(self, dim=4):
        self.dimension = dim

    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3, 0.4]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


@pytest.fixture
def temp_pipeline(tmp_path):
    qdrant_dir = tmp_path / "qdrant"
    upload_dir = tmp_path / "uploads"
    registry_path = tmp_path / "registry.json"

    store = VectorStore(storage_path=str(qdrant_dir), collection_name="test_pipeline")
    store.create_collection(vector_size=4)
    bm25 = BM25Index()
    embedder = DummyEmbedder(dim=4)

    pipeline = IngestionPipeline(
        vector_store=store,
        bm25_index=bm25,
        embedder=embedder,
        upload_dir=upload_dir,
        registry_path=registry_path
    )
    yield pipeline
    store.close()


def test_ingest_csv(temp_pipeline, tmp_path):
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text("item,category,price\nLaptop,Electronics,1200\nChair,Furniture,150\n", encoding="utf-8")

    result = temp_pipeline.ingest_file(str(csv_file))
    assert result["status"] == "success"
    assert result["chunks"] == 2
    assert result["filename"] == "test_data.csv"

    # Verify listing
    docs = temp_pipeline.list_documents()
    assert len(docs) == 1
    assert docs[0]["filename"] == "test_data.csv"
    assert docs[0]["total_chunks"] == 2


def test_duplicate_detection(temp_pipeline, tmp_path):
    csv_file = tmp_path / "dupe_test.csv"
    csv_file.write_text("colA,colB\nval1,val2\n", encoding="utf-8")

    res1 = temp_pipeline.ingest_file(str(csv_file))
    assert res1["status"] == "success"

    res2 = temp_pipeline.ingest_file(str(csv_file))
    assert res2["status"] == "duplicate"
    assert res2["document_id"] == res1["document_id"]


def test_delete_document(temp_pipeline, tmp_path):
    csv_file = tmp_path / "to_delete.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    res = temp_pipeline.ingest_file(str(csv_file))
    doc_id = res["document_id"]

    assert len(temp_pipeline.list_documents()) == 1

    deleted = temp_pipeline.delete_document(doc_id)
    assert deleted is True
    assert len(temp_pipeline.list_documents()) == 0
    assert temp_pipeline.bm25_index.count() == 0


def test_invalid_extension(temp_pipeline, tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Some text", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported format"):
        temp_pipeline.ingest_file(str(txt_file))
