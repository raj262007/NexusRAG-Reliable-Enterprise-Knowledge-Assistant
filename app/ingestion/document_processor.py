
from pathlib import Path

from app.ingestion.pdf_loader import load_pdf
from app.ingestion.docx_loader import load_docx
from app.ingestion.csv_loader import load_csv


SUPPORTED_FORMATS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".csv": load_csv,
}


def process_document(file_path: str) -> list[dict]:
    """
    Automatically detect document format
    and execute the appropriate loader.
    """

    path = Path(file_path)

    # Validate extension
    extension = path.suffix.lower()

    if extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {extension}"
        )

    # Validate file existence
    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    # Select and execute loader
    loader = SUPPORTED_FORMATS[extension]

    documents = loader(str(path))

    if not documents:
        raise ValueError("Document processing returned no data.")

    return documents
