
import pytest
from app.ingestion.pdf_loader import load_pdf


def test_missing_pdf():
    with pytest.raises(FileNotFoundError):
        load_pdf("missing.pdf")


def test_invalid_extension():
    with pytest.raises(ValueError):
        load_pdf("sample.txt")
