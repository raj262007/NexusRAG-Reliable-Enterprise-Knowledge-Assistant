
import re
from typing import Optional


def clean_text(text: str) -> str:
    """Normalize extracted text before chunking."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
) -> list[str]:
    """
    Split text into chunks with overlapping characters.

    chunk_size and overlap are measured in characters.
    """
    if not isinstance(text, str):
        raise TypeError("Text must be a string.")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size.")

    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to end at a word boundary.
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = end - overlap
        start = next_start

    return chunks


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 500,
    overlap: int = 100
) -> list[dict]:
    """
    Chunk extracted documents while preserving metadata.
    """
    all_chunks = []

    for document in documents:
        text = document.get("text", "")
        metadata = document.get("metadata", {})

        chunks = chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "metadata": {
                    **metadata,
                    "chunk_index": index,
                    "chunk_size": len(chunk)
                }
            })

    return all_chunks

