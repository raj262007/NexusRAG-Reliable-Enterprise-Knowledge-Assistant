
from pathlib import Path
import pymupdf as fitz


def load_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF while preserving page metadata.
    """

    path = Path(file_path)

    # Step 1: Validate file extension
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    # Step 2: Check whether file exists
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    documents = []

    try:
        with fitz.open(path) as pdf:

            # Step 3: Check encryption
            if pdf.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")

            # Step 4: Extract text page by page
            for page_number, page in enumerate(pdf, start=1):

                text = page.get_text("text").strip()

                if not text:
                    continue

                documents.append({
                    "text": text,
                    "metadata": {
                        "source": path.name,
                        "page": page_number,
                        "file_path": str(path.resolve())
                    }
                })

    except fitz.FileDataError as error:
        raise ValueError(
            f"Invalid or corrupted PDF: {error}"
        ) from error

    # Step 5: Check extracted content
    if not documents:
        raise ValueError("No extractable text found in PDF.")

    return documents
