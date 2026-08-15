from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Document, Page
from app.db.repositories import DocumentRepository
from app.ingestion.loader import PDFLoader
from app.ingestion.models import ParsedDocument
from app.ingestion.parser import PDFParser
from app.chunking.service import ChunkingService

class IngestionService:
    """Coordinates document loading and parsing."""

    def __init__( self, loader: PDFLoader | None = None, parser: PDFParser | None = None, chunking_service: ChunkingService | None = None ):
        self.loader = loader or PDFLoader()
        self.parser = parser or PDFParser()
        self.chunking_service = chunking_service or ChunkingService()

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

    def persist( self, parsed_document: ParsedDocument, db: Session ) -> Document:
        repository = DocumentRepository(db)

        existing = repository.get_by_hash(
            parsed_document.file_hash
        )

        if existing:
            return existing

        document = Document(
            filename=parsed_document.filename,
            title=parsed_document.title,
            author=parsed_document.author,
            subject=parsed_document.subject,
            file_hash=parsed_document.file_hash,
            file_size=parsed_document.file_size,
            page_count=parsed_document.page_count,
            created_at=parsed_document.created_at,
            department=None,
            year=None,
            language=None,
            tags=[],
        )

        repository.create(document)

        for page in parsed_document.pages:
            document.pages.append(
                Page(
                    page_number=page.page_number,
                    text=page.text,
                )
            )

        repository.save()

        return document

    def ingest_and_persist( self, file_path: str | Path, db: Session ) -> Document:
        parsed_document = self.ingest(file_path)
        document = self.persist(parsed_document,db)
        self.chunking_service.chunk_document(document, db)

        return document