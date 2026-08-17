import pytest

from app.retrieval.bm25 import BM25RetrievalService, tokenize
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

def test_tokenize_preserves_technical_tokens():
    assert tokenize("ERR_CONNECTION_RESET on Python 3.12") == [
        "err_connection_reset",
        "on",
        "python",
        "3.12",
    ]

def test_bm25_ranks_exact_technical_match_first():
    service = BM25RetrievalService()

    service.build_index_from_chunks([
        make_chunk(
            1,
            "Employees must use passwords with twelve characters.",
        ),
        make_chunk(
            2,
            "The client received ERR_CONNECTION_RESET during the request.",
        ),
        make_chunk(
            3,
            "Office parking rules apply to all staff.",
        ),
    ])

    results = service.search("ERR_CONNECTION_RESET", top_k=2)

    assert [result.chunk_id for result in results] == [2]
    assert results[0].score > 0

def test_bm25_returns_no_results_when_no_terms_match():
    service = BM25RetrievalService()

    service.build_index_from_chunks([
        make_chunk(1, "Employee password policy."),
        make_chunk(2, "Office parking rules."),
    ])

    assert service.search("quantum entanglement") == []

def test_search_requires_built_index():
    service = BM25RetrievalService()

    with pytest.raises(RuntimeError, match="BM25 index is not built"):
        service.search("password")

def test_invalid_bm25_parameters_fail_fast():
    with pytest.raises(ValueError, match="k1 must be positive"):
        BM25RetrievalService(k1=0)

    with pytest.raises(ValueError, match="b must be between 0 and 1"):
        BM25RetrievalService(b=1.1)