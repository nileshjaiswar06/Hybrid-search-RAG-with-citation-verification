from sqlalchemy.orm import Session

from app.core.config import settings
from app.reranking.client import CrossEncoderReranker, Reranker
from app.retrieval.hybrid import HybridRetrievalService
from app.retrieval.models import RerankedChunk

class RerankingService:
    """Retrieves hybrid candidates and reranks them with a cross-encoder."""
    def __init__(self, *, hybrid_service: HybridRetrievalService | None = None, reranker: Reranker | None = None) -> None:
        self.hybrid_service = hybrid_service or HybridRetrievalService()
        self.reranker = reranker or CrossEncoderReranker()

    def search(self, query: str, db: Session, *, top_k: int | None = None, candidate_k: int | None = None) -> list[RerankedChunk]:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        result_limit = (
            settings.reranker_default_top_k
            if top_k is None
            else top_k
        )

        retrieval_limit = (
            settings.reranker_candidate_k
            if candidate_k is None
            else candidate_k
        )

        if result_limit <= 0:
            raise ValueError("top_k must be positive.")

        if retrieval_limit <= 0:
            raise ValueError("candidate_k must be positive.")

        hybrid_candidates = self.hybrid_service.search(
            cleaned_query,
            db,
            top_k=retrieval_limit,
            candidate_k=settings.hybrid_candidate_k,
        )

        if not hybrid_candidates:
            return []

        reranker_scores = self.reranker.score(
            cleaned_query,
            [candidate.text for candidate in hybrid_candidates],
        )

        if len(reranker_scores) != len(hybrid_candidates):
            raise RuntimeError(
                "Reranker returned a score count that does not match candidates."
            )

        scored_candidates = [
            RerankedChunk(
                chunk_id=candidate.chunk_id,
                document_id=candidate.document_id,
                filename=candidate.filename,
                page_number=candidate.page_number,
                chunk_index=candidate.chunk_index,
                text=candidate.text,
                reranker_score=score,
                hybrid_rank=hybrid_rank,
                rrf_score=candidate.rrf_score,
                dense_rank=candidate.dense_rank,
                bm25_rank=candidate.bm25_rank,
                retrieved_by=candidate.retrieved_by,
            )
            for hybrid_rank, (candidate, score) in enumerate(
                zip(hybrid_candidates, reranker_scores, strict=True),
                start=1,
            )
        ]

        ranked_candidates = sorted(
            scored_candidates,
            key=lambda item: (
                -item.reranker_score,
                item.hybrid_rank,
                item.chunk_id,
            ),
        )

        return ranked_candidates[:result_limit]