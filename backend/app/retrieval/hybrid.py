from dataclasses import dataclass
from typing import Sequence

from sqlalchemy.orm import Session

from app.core.config import settings
from app.retrieval.bm25 import BM25RetrievalService
from app.retrieval.models import HybridRetrievedChunk, RetrievedChunk
from app.retrieval.service import DenseRetrievalService

@dataclass
class _FusionState:
    chunk: RetrievedChunk
    rrf_score: float = 0.0
    dense_rank: int | None = None
    bm25_rank: int | None = None

def reciprocal_rank_fusion(
    dense_results: Sequence[RetrievedChunk],
    bm25_results: Sequence[RetrievedChunk],
    *,
    rrf_k: int = 60,
) -> list[HybridRetrievedChunk]:
    """Fuse dense and BM25 rankings using Reciprocal Rank Fusion."""
    if rrf_k <= 0:
        raise ValueError("rrf_k must be positive.")

    states: dict[int, _FusionState] = {}

    for rank, chunk in enumerate(dense_results, start=1):
        state = states.setdefault(
            chunk.chunk_id,
            _FusionState(chunk=chunk),
        )

        state.rrf_score += 1 / (rrf_k + rank)
        state.dense_rank = rank

    for rank, chunk in enumerate(bm25_results, start=1):
        state = states.setdefault(
            chunk.chunk_id,
            _FusionState(chunk=chunk),
        )

        state.rrf_score += 1 / (rrf_k + rank)
        state.bm25_rank = rank

    fused_results = [
        HybridRetrievedChunk(
            chunk_id=state.chunk.chunk_id,
            document_id=state.chunk.document_id,
            filename=state.chunk.filename,
            page_number=state.chunk.page_number,
            chunk_index=state.chunk.chunk_index,
            text=state.chunk.text,
            rrf_score=state.rrf_score,
            dense_rank=state.dense_rank,
            bm25_rank=state.bm25_rank,
            retrieved_by=tuple(
                source
                for source, rank in (
                    ("dense", state.dense_rank),
                    ("bm25", state.bm25_rank),
                )
                if rank is not None
            ),
        )
        for state in states.values()
    ]

    return sorted(
        fused_results,
        key=lambda item: (
            -item.rrf_score,
            min(
                rank
                for rank in (item.dense_rank, item.bm25_rank)
                if rank is not None
            ),
            item.chunk_id,
        ),
    )


class HybridRetrievalService:
    """Combines dense and BM25 retrieval with Reciprocal Rank Fusion."""
    def __init__(
        self,
        *,
        dense_service: DenseRetrievalService | None = None,
        bm25_service: BM25RetrievalService | None = None,
    ) -> None:
        self.dense_service = dense_service or DenseRetrievalService()
        self.bm25_service = bm25_service or BM25RetrievalService()

    def search(self, query: str, db: Session, *, top_k: int | None = None, candidate_k: int | None = None) -> list[HybridRetrievedChunk]:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        result_limit = (
            settings.hybrid_default_top_k
            if top_k is None
            else top_k
        )

        retrieval_limit = (
            settings.hybrid_candidate_k
            if candidate_k is None
            else candidate_k
        )

        if result_limit <= 0:
            raise ValueError("top_k must be positive.")

        if retrieval_limit <= 0:
            raise ValueError("candidate_k must be positive.")

        dense_results = self.dense_service.search(
            cleaned_query,
            db,
            top_k=retrieval_limit,
        )

        self.bm25_service.build_index(db)

        bm25_results = self.bm25_service.search(
            cleaned_query,
            top_k=retrieval_limit,
        )

        fused_results = reciprocal_rank_fusion(
            dense_results,
            bm25_results,
            rrf_k=settings.rrf_k,
        )

        return fused_results[:result_limit]