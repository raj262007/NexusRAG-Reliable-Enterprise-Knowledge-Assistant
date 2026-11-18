
import pytest
from docx import Document
from app.ingestion.docx_loader import load_docx


def test_missing_docx():
    with pytest.raises(FileNotFoundError):
        load_docx("missing.docx")


def test_invalid_extension():
    with pytest.raises(ValueError):
        load_docx("sample.pdf")


def test_docx_extraction(tmp_path):
    file_path = tmp_path / "sample.docx"

    doc = Document()
    doc.add_paragraph("NexusRAG is an AI project.")

    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Technology"
    table.cell(0, 1).text = "Python"

    doc.save(file_path)

    result = load_docx(str(file_path))

    assert len(result) == 2
    assert "NexusRAG" in result[0]["text"]
    assert "Python" in result[1]["text"]
    assert result[0]["metadata"]["type"] == "paragraph"
    assert result[1]["metadata"]["type"] == "table"
