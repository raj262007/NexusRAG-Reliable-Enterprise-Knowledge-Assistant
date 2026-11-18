import io
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, UploadFile

from app.api.main import root
from app.api.routes import (
    health_check,
    get_system_status,
    upload_document,
    list_documents,
    query_documents,
    chat_documents,
    delete_document,
    clear_chat_session,
    list_models,
)
from app.api.schemas import QueryRequest
from app.api.services import services


class DummyApiEmbedder:
    dimension = 384

    def embed_text(self, text: str):
        return [0.05] * 384

    def embed_texts(self, texts: list[str], batch_size: int = 32):
        return [[0.05] * 384 for _ in texts]


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock Ollama and embedder during API integration tests so tests run offline in seconds."""
    original_ollama = services._ollama_client
    original_embedder = services._embedder

    mock_ollama = MagicMock()
    mock_ollama.default_model = "qwen2.5:3b"
    mock_ollama.is_available.return_value = True
    mock_ollama.list_models.return_value = ["qwen2.5:3b"]
    mock_ollama.check_status.return_value = {
        "available": True,
        "base_url": "http://localhost:11434",
        "configured_model": "qwen2.5:3b",
        "installed_models": ["qwen2.5:3b"],
        "model_ready": True,
        "instructions": None
    }
    mock_ollama.generate.return_value = "This is a factual answer [Source: sample.csv, Row 1]."
    services._ollama_client = mock_ollama
    services._embedder = DummyApiEmbedder()

    yield

    services._ollama_client = original_ollama
    services._embedder = original_embedder


def test_root_endpoint():
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "application/json"
    res = root(mock_request)
    assert res["project"] == "NexusRAG"
    assert "/docs" in res["docs"]


def test_health_check():
    res = health_check()
    assert res.status == "healthy"
    assert res.ollama_connected is True
    assert res.configured_model == "qwen2.5:3b"


def test_status_endpoint():
    res = get_system_status()
    assert res.project_name == "NexusRAG"
    assert res.embedding_model is not None


def test_upload_invalid_extension():
    fake_file = UploadFile(filename="malicious.exe", file=io.BytesIO(b"binary content"))
    with pytest.raises(HTTPException) as exc_info:
        upload_document(file=fake_file)
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail


def test_upload_and_delete_flow():
    csv_bytes = b"feature,description\nHybrid Search,Dense vector plus BM25 search\nLocal Ollama,Private local LLM inference\n"
    fake_file = UploadFile(filename="test_features.csv", file=io.BytesIO(csv_bytes))

    # 1. Upload
    upload_res = upload_document(file=fake_file)
    assert upload_res.status in ("success", "duplicate")
    doc_id = upload_res.document_id

    # 2. List
    docs = list_documents()
    assert any(d.document_id == doc_id for d in docs)

    # 3. Query
    q_req = QueryRequest(question="What is hybrid search?", top_k=2)
    q_res = query_documents(q_req)
    assert q_res.answer is not None
    assert q_res.model == "qwen2.5:3b"

    # 4. Chat
    c_req = QueryRequest(question="Explain local Ollama", top_k=2)
    c_res = chat_documents(c_req)
    assert c_res.session_id is not None

    # 5. Clear chat session
    cleared = clear_chat_session(c_res.session_id)
    assert cleared["cleared"] is True

    # 6. Delete document
    del_res = delete_document(doc_id)
    assert del_res.success is True
    assert del_res.document_id == doc_id


def test_list_models():
    res = list_models()
    assert res["available"] is True
    assert "qwen2.5:3b" in res["installed_models"]
