import pytest

from app.generation.citations import resolve_citations
from app.generation.context import ContextBuilder
from app.retrieval.models import RerankedChunk


def make_chunk(
    chunk_id: int,
    filename: str,
    page_number: int,
) -> RerankedChunk:
    return RerankedChunk(
        chunk_id=chunk_id,
        document_id=1,
        filename=filename,
        page_number=page_number,
        chunk_index=chunk_id,
        text=f"Evidence from chunk {chunk_id}.",
        reranker_score=0.9,
        hybrid_rank=1,
        rrf_score=0.03,
        dense_rank=1,
        bm25_rank=1,
        retrieved_by=("dense", "bm25"),
    )


def test_resolve_citations_maps_labels_to_real_chunks():
    context = ContextBuilder(max_chars=2000).build([
        make_chunk(10, "policy.pdf", 3),
        make_chunk(20, "handbook.pdf", 8),
    ])

    citations = resolve_citations(
        "Passwords must be strong. [1] More rules apply. [2]",
        context,
        require_citations=True,
    )

    assert [citation.label for citation in citations] == [1, 2]
    assert citations[0].chunk_id == 10
    assert citations[0].filename == "policy.pdf"
    assert citations[1].chunk_id == 20
    assert citations[1].page_number == 8


def test_resolve_citations_removes_duplicates_but_keeps_order():
    context = ContextBuilder(max_chars=2000).build([
        make_chunk(10, "policy.pdf", 3),
        make_chunk(20, "handbook.pdf", 8),
    ])

    citations = resolve_citations(
        "First claim. [2] Second claim. [1] Third claim. [2]",
        context,
        require_citations=True,
    )

    assert [citation.label for citation in citations] == [2, 1]


def test_resolve_citations_rejects_unknown_label():
    context = ContextBuilder(max_chars=2000).build([
        make_chunk(10, "policy.pdf", 3),
    ])

    with pytest.raises(
        RuntimeError,
        match=r"citation IDs not present in context: \[2\]",
    ):
        resolve_citations(
            "Unsupported citation. [2]",
            context,
            require_citations=True,
        )


def test_resolve_citations_requires_at_least_one_citation():
    context = ContextBuilder(max_chars=2000).build([
        make_chunk(10, "policy.pdf", 3),
    ])

    with pytest.raises(
        RuntimeError,
        match="contains no citations",
    ):
        resolve_citations(
            "This answer has no citation.",
            context,
            require_citations=True,
        )

def test_no_answer_can_have_no_citations():
    context = ContextBuilder(max_chars=2000).build([
        make_chunk(10, "policy.pdf", 3),
    ])

    citations = resolve_citations(
        "I don't know based on the provided documents.",
        context,
        require_citations=False,
    )

    assert citations == ()