import re
from collections.abc import Callable, Sequence
from dataclasses import replace

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Chunk, Document, Page
from app.retrieval.models import RetrievedChunk

TOKEN_PATTERN = re.compile(
    r"[a-z0-9]+(?:[._/-][a-z0-9]+)*",
    re.IGNORECASE,
)

def tokenize(text: str) -> list[str]:
    """Turn text into stable lexical-search tokens."""
    return TOKEN_PATTERN.findall(text.lower())

class BM25RetrievalService:
    """Builds an in-memory BM25 index and searches it."""
    def __init__(self, *, k1: float | None = None, b: float | None = None, tokenizer: Callable[[str], list[str]] = tokenize) -> None:
        self.k1 = settings.bm25_k1 if k1 is None else k1
        self.b = settings.bm25_b if b is None else b
        self.tokenizer = tokenizer

        if self.k1 <= 0:
            raise ValueError("BM25 k1 must be positive.")

        if not 0 <= self.b <= 1:
            raise ValueError("BM25 b must be between 0 and 1.")

        self._bm25: BM25Okapi | None = None
        self._indexed_chunks: list[RetrievedChunk] = []

    def build_index(self, db: Session) -> int:
        """Load all chunks from PostgreSQL and build the BM25 index."""

        statement = (
            select(Chunk, Document, Page)
            .join(Page, Chunk.page_id == Page.id)
            .join(Document, Chunk.document_id == Document.id)
            .order_by(
                Document.id,
                Page.page_number,
                Chunk.chunk_index,
            )
        )

        rows = db.execute(statement).all()

        chunks = [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                filename=document.filename,
                page_number=page.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                score=0.0,
            )
            for chunk, document, page in rows
        ]

        return self.build_index_from_chunks(chunks)

    def build_index_from_chunks(self, chunks: Sequence[RetrievedChunk]) -> int:
        """Build an index from chunks; useful for tests as well."""
        self._indexed_chunks = list(chunks)

        if not self._indexed_chunks:
            self._bm25 = None
            return 0

        tokenized_corpus = [
            self.tokenizer(chunk.text)
            for chunk in self._indexed_chunks
        ]

        self._bm25 = BM25Okapi(
            tokenized_corpus,
            k1=self.k1,
            b=self.b,
        )

        return len(self._indexed_chunks)

    def search(self, query: str, *, top_k: int | None = None) -> list[RetrievedChunk]:
        """Return chunks with positive BM25 scores, highest first."""
        if self._bm25 is None:
            raise RuntimeError(
                "BM25 index is not built. Call build_index() before search()."
            )

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        limit = (
            settings.bm25_default_top_k
            if top_k is None
            else top_k
        )

        if limit <= 0:
            raise ValueError("top_k must be positive.")

        query_tokens = self.tokenizer(cleaned_query)

        if not query_tokens:
            raise ValueError("Query must contain searchable terms.")

        scores = self._bm25.get_scores(query_tokens)

        ranked_indexes = sorted(
            (
                index
                for index, score in enumerate(scores)
                if score > 0
            ),
            key=lambda index: (
                -float(scores[index]),
                self._indexed_chunks[index].chunk_id,
            ),
        )

        return [
            replace(
                self._indexed_chunks[index],
                score=float(scores[index]),
            )
            for index in ranked_indexes[:limit]
        ]