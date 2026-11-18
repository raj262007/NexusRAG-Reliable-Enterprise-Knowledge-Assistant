
import pytest
from app.ingestion.csv_loader import load_csv


def test_missing_csv():
    with pytest.raises(FileNotFoundError):
        load_csv("missing.csv")


def test_invalid_extension():
    with pytest.raises(ValueError):
        load_csv("sample.pdf")


def test_csv_extraction(tmp_path):
    file_path = tmp_path / "sample.csv"

    file_path.write_text(
        "name,technology\n"
        "NexusRAG,Python\n"
        "VoiceAgent,PyTorch\n",
        encoding="utf-8"
    )

    result = load_csv(str(file_path))

    assert len(result) == 2
    assert "NexusRAG" in result[0]["text"]
    assert "Python" in result[0]["text"]
    assert result[0]["metadata"]["row"] == 1


def test_empty_csv(tmp_path):
    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        load_csv(str(file_path))
