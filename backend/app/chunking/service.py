from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chunking.splitter import TextChunker
from app.db.models import Chunk, Document

class ChunkingService:
    def __init__(self, chunker: TextChunker | None = None):
        self.chunker = (chunker or TextChunker())

    def chunk_document(self, document: Document, db: Session) -> list[Chunk]:
        existing = db.scalars(
            select(Chunk).where(Chunk.document_id == document.id).limit(1)
        ).first()

        if existing:
            return list(
                db.scalars(select(Chunk).where(Chunk.document_id == document.id)).all()
        )
        
        created_chunks: list[Chunk] = []

        for page in document.pages:
            chunks = self.chunker.chunk(page.text)

            for chunk_data in chunks:
                chunk = Chunk(
                    document_id=document.id,
                    page_id=page.id,
                    chunk_index=chunk_data.chunk_index,
                    text=chunk_data.text,
                    start_char=chunk_data.start_char,
                    end_char=chunk_data.end_char,
                    metadata_json={
                        "page_number": page.page_number,
                        "chunking_version": "v1"
                    },
                )

                db.add(chunk)
                created_chunks.append(chunk)

        db.commit()

        return created_chunks