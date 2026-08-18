import pytest

from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.models import RetrievedChunk

def make_chunk(chunk_id: int, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=1,
        filename="test.pdf",
        page_number=1,
        chunk_index=chunk_id,
        text=text,
        score=0.0,
    )


def test_rrf_boosts_chunk_found_by_both_retrievers():
    dense_results = [
        make_chunk(1, "Dense-only result"),
        make_chunk(2, "Shared result"),
    ]

    bm25_results = [
        make_chunk(2, "Shared result"),
        make_chunk(3, "BM25-only result"),
    ]

    results = reciprocal_rank_fusion(
        dense_results,
        bm25_results,
        rrf_k=60,
    )

    assert [result.chunk_id for result in results] == [2, 1, 3]

    shared = results[0]
    assert shared.dense_rank == 2
    assert shared.bm25_rank == 1
    assert shared.retrieved_by == ("dense", "bm25")


def test_rrf_keeps_single_retriever_provenance():
    results = reciprocal_rank_fusion(
        [make_chunk(1, "Dense result")],
        [],
    )

    assert len(results) == 1
    assert results[0].chunk_id == 1
    assert results[0].dense_rank == 1
    assert results[0].bm25_rank is None
    assert results[0].retrieved_by == ("dense",)


def test_rrf_returns_empty_list_when_both_lists_are_empty():
    assert reciprocal_rank_fusion([], []) == []


def test_rrf_rejects_invalid_constant():
    with pytest.raises(ValueError, match="rrf_k must be positive"):
        reciprocal_rank_fusion([], [], rrf_k=0)