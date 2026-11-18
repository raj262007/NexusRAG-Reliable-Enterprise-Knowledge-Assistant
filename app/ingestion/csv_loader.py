
from pathlib import Path
import pandas as pd


def load_csv(file_path: str) -> list[dict]:
    """
    Extract CSV rows into text documents with metadata.
    """

    path = Path(file_path)

    # Step 1: Validate extension
    if path.suffix.lower() != ".csv":
        raise ValueError("Only CSV files are supported.")

    # Step 2: Check file existence
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {file_path}")

    try:
        # Step 3: Read CSV
        df = pd.read_csv(path)

        if df.empty:
            raise ValueError("CSV file contains no data rows.")

        if len(df.columns) == 0:
            raise ValueError("CSV contains no columns.")

        documents = []

        # Step 4: Convert each row into text
        for row_index, row in df.iterrows():

            row_data = []

            for column in df.columns:
                value = row[column]

                if pd.isna(value):
                    continue

                row_data.append(f"{column}: {value}")

            if not row_data:
                continue

            text = " | ".join(row_data)

            documents.append({
                "text": text,
                "metadata": {
                    "source": path.name,
                    "type": "csv_row",
                    "row": int(row_index) + 1,
                    "columns": list(df.columns),
                    "file_path": str(path.resolve())
                }
            })

    except pd.errors.EmptyDataError as error:
        raise ValueError("CSV file is empty.") from error

    except pd.errors.ParserError as error:
        raise ValueError(f"Invalid CSV format: {error}") from error

    if not documents:
        raise ValueError("No extractable data found in CSV.")

    return documents
