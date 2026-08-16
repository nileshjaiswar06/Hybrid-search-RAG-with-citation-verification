from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Chunk, ChunkEmbedding, Document, Page
from app.embeddings.client import EmbeddingClient, GeminiEmbeddingClient
from app.retrieval.models import RetrievedChunk

class DenseRetrievalService:
    """Retrieves document chunks using cosine similarity."""

    def __init__(self, client: EmbeddingClient | None = None) -> None:
        self.client = client or GeminiEmbeddingClient()

    def search(self, query: str, db: Session, *, top_k: int | None = None) -> list[RetrievedChunk]:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        limit = (
            settings.dense_retrieval_default_top_k
            if top_k is None else top_k
        )

        if limit <= 0:
            raise ValueError("top_k must be positive.")

        vectors = self.client.embed_queries([cleaned_query])

        if len(vectors) != 1:
            raise RuntimeError(
                "Query embedding client must return exactly one vector."
            )

        query_vector = vectors[0]

        if len(query_vector) != settings.embedding_dimensions:
            raise RuntimeError(
                "Query embedding has an unexpected number of dimensions."
            )

        cosine_distance = ChunkEmbedding.embedding.cosine_distance(
            query_vector
        ).label("cosine_distance")

        statement = (
            select(Chunk, Document, Page, cosine_distance)
            .join(Chunk, ChunkEmbedding.chunk_id == Chunk.id)
            .join(Page, Chunk.page_id == Page.id)
            .join(Document, Chunk.document_id == Document.id)
            .order_by(cosine_distance)
            .limit(limit)
        )

        rows = db.execute(statement).all()

        return [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                filename=document.filename,
                page_number=page.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                score=1.0 - float(distance),
            )
            for chunk, document, page, distance in rows
        ]