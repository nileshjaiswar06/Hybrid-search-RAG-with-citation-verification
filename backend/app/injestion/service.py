from pathlib import Path

from app.injestion.loader import PDFLoader
from app.injestion.models import ParsedDocument
from app.injestion.parser import PDFParser

class IngestionService:
    """Coordinates document loading and parsing."""

    def __init__( self, loader: PDFLoader | None = None, parser: PDFParser | None = None ):
        self.loader = loader or PDFLoader()
        self.parser = parser or PDFParser()

    def ingest( self, file_path: str | Path ) -> ParsedDocument:
        path = Path(file_path)
        pdf = self.loader.load(path)

        try:
            return self.parser.parse(
                pdf,
                path,
            )
        finally:
            pdf.close()