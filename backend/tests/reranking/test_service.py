import pytest

from app.reranking.service import RerankingService
from app.retrieval.models import HybridRetrievedChunk


def make_candidate(
    chunk_id: int,
    text: str,
    *,
    rrf_score: float,
) -> HybridRetrievedChunk:
    return HybridRetrievedChunk(
        chunk_id=chunk_id,
        document_id=1,
        filename="test.pdf",
        page_number=1,
        chunk_index=chunk_id,
        text=text,
        rrf_score=rrf_score,
        dense_rank=chunk_id,
        bm25_rank=None,
        retrieved_by=("dense",),
    )


class FakeHybridService:
    def __init__(self, candidates: list[HybridRetrievedChunk]) -> None:
        self.candidates = candidates
        self.calls = []

    def search(self, query, db, *, top_k, candidate_k):
        self.calls.append((query, top_k, candidate_k))
        return self.candidates[:top_k]


class FakeReranker:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.calls = []

    def score(self, query, passages):
        self.calls.append((query, list(passages)))
        return self.scores


def test_reranker_changes_hybrid_order():
    hybrid_service = FakeHybridService([
        make_candidate(1, "First hybrid result", rrf_score=0.03),
        make_candidate(2, "Second hybrid result", rrf_score=0.02),
    ])

    reranker = FakeReranker([0.2, 0.9])

    service = RerankingService(
        hybrid_service=hybrid_service,
        reranker=reranker,
    )

    results = service.search(
        "Which chunk is best?",
        db=object(),
        top_k=2,
        candidate_k=2,
    )

    assert [result.chunk_id for result in results] == [2, 1]
    assert results[0].hybrid_rank == 2
    assert results[0].reranker_score == 0.9


def test_reranking_returns_empty_when_hybrid_returns_empty():
    service = RerankingService(
        hybrid_service=FakeHybridService([]),
        reranker=FakeReranker([]),
    )

    assert service.search(
        "Any question",
        db=object(),
        top_k=5,
        candidate_k=20,
    ) == []


def test_reranking_rejects_invalid_limits():
    service = RerankingService(
        hybrid_service=FakeHybridService([]),
        reranker=FakeReranker([]),
    )

    with pytest.raises(ValueError, match="top_k must be positive"):
        service.search(
            "Question",
            db=object(),
            top_k=0,
        )

    with pytest.raises(ValueError, match="candidate_k must be positive"):
        service.search(
            "Question",
            db=object(),
            candidate_k=0,
        )


def test_reranking_rejects_wrong_score_count():
    hybrid_service = FakeHybridService([
        make_candidate(1, "Candidate one", rrf_score=0.03),
        make_candidate(2, "Candidate two", rrf_score=0.02),
    ])

    service = RerankingService(
        hybrid_service=hybrid_service,
        reranker=FakeReranker([0.9]),
    )

    with pytest.raises(
        RuntimeError,
        match="Reranker returned a score count that does not match candidates.",
    ):
        service.search(
            "Question",
            db=object(),
            top_k=2,
            candidate_k=2,
        )