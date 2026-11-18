
import pytest

from docx import Document

from app.ingestion.document_processor import process_document


def test_unsupported_format():
    with pytest.raises(ValueError):
        process_document("sample.txt")


def test_missing_document():
    with pytest.raises(FileNotFoundError):
        process_document("missing.pdf")


def test_pdf_dispatch(tmp_path):
    import pymupdf as fitz

    file_path = tmp_path / "sample.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((50, 50), "NexusRAG PDF Test")
    pdf.save(file_path)
    pdf.close()

    result = process_document(str(file_path))

    assert len(result) == 1
    assert "NexusRAG" in result[0]["text"]


def test_docx_dispatch(tmp_path):
    file_path = tmp_path / "sample.docx"

    doc = Document()
    doc.add_paragraph("NexusRAG DOCX Test")
    doc.save(file_path)

    result = process_document(str(file_path))

    assert len(result) == 1
    assert "NexusRAG" in result[0]["text"]


def test_csv_dispatch(tmp_path):
    file_path = tmp_path / "sample.csv"

    file_path.write_text(
        "name,language\nNexusRAG,Python\n",
        encoding="utf-8"
    )

    result = process_document(str(file_path))

    assert len(result) == 1
    assert "Python" in result[0]["text"]
