from pathlib import Path

import fitz

class PDFLoader:
    """Loads a PDF file using PyMuPDF."""

    def load(self, file_path: str | Path) -> fitz.Document:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF file does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file, got: {path.suffix}"
            )

        return fitz.open(path)