
import pytest

from app.ingestion.chunker import (
    clean_text,
    chunk_text,
    chunk_documents
)


def test_clean_text():
    text = "Hello     world\n\nPython"
    assert clean_text(text) == "Hello world Python"


def test_empty_text():
    assert chunk_text("") == []


def test_single_chunk():
    text = "This is a short document."
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_multiple_chunks():
    text = " ".join(["Python"] * 100)
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("Hello world", chunk_size=0)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("Hello world", chunk_size=100, overlap=100)


def test_chunk_documents_metadata():
    documents = [{
        "text": " ".join(["AI"] * 100),
        "metadata": {
            "source": "sample.pdf",
            "page": 1
        }
    }]

    chunks = chunk_documents(
        documents,
        chunk_size=50,
        overlap=10
    )

    assert len(chunks) > 1
    assert chunks[0]["metadata"]["source"] == "sample.pdf"
    assert chunks[0]["metadata"]["page"] == 1
    assert chunks[0]["metadata"]["chunk_index"] == 0
