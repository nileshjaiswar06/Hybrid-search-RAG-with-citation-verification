import hashlib
from datetime import datetime, timezone
from pathlib import Path

import fitz

from app.ingestion.models import PageContent, ParsedDocument

def normalize_text(text: str) -> str:
    """Normalize extracted PDF text without changing its meaning."""

    lines = [
        line.strip()
        for line in text.splitlines()
    ]

    lines = [
        line for line in lines if line
    ]

    return "\n".join(lines)

class PDFParser:
    """Converts a PyMuPDF document into our internal representation."""

    def parse(self, pdf: fitz.Document, file_path: str | Path ) -> ParsedDocument:
        path = Path(file_path)
        metadata = pdf.metadata or {}
        pages: list[PageContent] = []

        for index, page in enumerate(pdf):
            text = normalize_text(page.get_text("text"))

            pages.append(
                PageContent(
                    page_number=index + 1,
                    text=text,
                    metadata={
                        "width": page.rect.width,
                        "height": page.rect.height,
                        # "has_text": bool(text.strip()),
                    },
                )
            )

        return ParsedDocument(
            filename=path.name,
            file_path=str(path),
            title=metadata.get("title") or None,
            author=metadata.get("author") or None,
            subject=metadata.get("subject") or None,
            page_count=len(pages),
            file_size=path.stat().st_size,
            file_hash=self._calculate_file_hash(path),
            created_at=datetime.now(timezone.utc),
            pages=pages,
        )

    @staticmethod
    def _calculate_file_hash( file_path: Path ) -> str:
        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(block)

        return sha256.hexdigest()