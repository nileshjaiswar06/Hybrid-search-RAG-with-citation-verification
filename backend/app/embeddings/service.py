import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.models import Chunk, ChunkEmbedding, Document
from app.embeddings.client import (
    EmbeddingClient,
    GeminiEmbeddingClient,
    prepare_document,
)

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

class EmbeddingService:
    """Generates and persists exactly one current vector for each chunk."""
    def __init__(self, client: EmbeddingClient | None = None, *, batch_size: int = 32):
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        self.client = client or GeminiEmbeddingClient()
        self.batch_size = batch_size

    def embed_document(self, document_id: int, db: Session) -> int:
        document = db.scalar(
            select(Document).where(Document.id == document_id)
        )

        if document is None:
            raise ValueError(f"Document {document_id} does not exist.")

        chunks = list(
            db.scalars(
                select(Chunk)
                .where(Chunk.document_id == document_id)
                .options(selectinload(Chunk.document))
                .order_by(Chunk.page_id, Chunk.chunk_index)
            )
        )

        if not chunks:
            raise ValueError(f"Document {document_id} has no chunks to embed.")

        existing_by_chunk = {
            item.chunk_id: item
            for item in db.scalars(
                select(ChunkEmbedding).where(
                    ChunkEmbedding.chunk_id.in_([chunk.id for chunk in chunks])
                )
            )
        }

        pending = [
            chunk
            for chunk in chunks
            if self._needs_embedding(
                chunk,
                existing_by_chunk.get(chunk.id),
            )
        ]

        for start in range(0, len(pending), self.batch_size):
            batch = pending[start:start + self.batch_size]

            inputs = [
                prepare_document(
                    chunk.text,
                    document.title or document.filename,
                )
                for chunk in batch
            ]

            vectors = self.client.embed_documents(inputs)

            for chunk, vector in zip(batch, vectors, strict=True):
                item = existing_by_chunk.get(chunk.id)

                if item is None:
                    item = ChunkEmbedding(chunk_id=chunk.id)
                    db.add(item)

                item.embedding = vector
                item.model_name = settings.gemini_embedding_model
                item.dimensions = settings.embedding_dimensions
                item.content_hash = hash_content(chunk.text)
                item.created_at = datetime.now(timezone.utc)

        db.commit()
        return len(pending)

    @staticmethod
    def _needs_embedding(chunk: Chunk, existing: ChunkEmbedding | None) -> bool:
        return existing is None or any((
            existing.content_hash != hash_content(chunk.text),
            existing.model_name != settings.gemini_embedding_model,
            existing.dimensions != settings.embedding_dimensions,
        ))