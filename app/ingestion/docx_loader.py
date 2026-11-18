
from pathlib import Path
from docx import Document


def load_docx(file_path: str) -> list[dict]:
    """
    Extract text from DOCX files including paragraphs and tables.
    """

    path = Path(file_path)

    # Step 1: Validate extension
    if path.suffix.lower() != ".docx":
        raise ValueError("Only DOCX files are supported.")

    # Step 2: Check file existence
    if not path.exists():
        raise FileNotFoundError(f"DOCX not found: {file_path}")

    documents = []

    try:
        doc = Document(path)

        # Step 3: Extract paragraphs
        for index, paragraph in enumerate(doc.paragraphs, start=1):

            text = paragraph.text.strip()

            if not text:
                continue

            documents.append({
                "text": text,
                "metadata": {
                    "source": path.name,
                    "type": "paragraph",
                    "index": index,
                    "file_path": str(path.resolve())
                }
            })

        # Step 4: Extract tables
        for table_index, table in enumerate(doc.tables, start=1):

            for row_index, row in enumerate(table.rows, start=1):

                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells
                )

                if not row_text.strip(" |"):
                    continue

                documents.append({
                    "text": row_text,
                    "metadata": {
                        "source": path.name,
                        "type": "table",
                        "table": table_index,
                        "row": row_index,
                        "file_path": str(path.resolve())
                    }
                })

    except Exception as error:
        raise ValueError(
            f"Unable to read DOCX file: {error}"
        ) from error

    # Step 5: Validate extracted content
    if not documents:
        raise ValueError("No extractable text found in DOCX.")

    return documents
