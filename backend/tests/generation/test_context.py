from app.generation.context import ContextBuilder
from app.retrieval.models import RerankedChunk

def make_chunk(chunk_id: int, text: str) -> RerankedChunk:
    return RerankedChunk(
        chunk_id=chunk_id,
        document_id=1,
        filename="policy.pdf",
        page_number=3,
        chunk_index=chunk_id,
        text=text,
        reranker_score=0.9,
        hybrid_rank=1,
        rrf_score=0.03,
        dense_rank=1,
        bm25_rank=1,
        retrieved_by=("dense", "bm25"),
    )

def test_context_builder_keeps_source_metadata():
    context = ContextBuilder(max_chars=1000).build([
        make_chunk(42, "Employees must use strong passwords."),
    ])

    assert len(context.chunks) == 1
    assert 'chunk_id="42"' in context.text
    assert 'source="policy.pdf"' in context.text
    assert 'page="3"' in context.text
    assert "Employees must use strong passwords." in context.text

def test_context_builder_respects_budget():
    context = ContextBuilder(max_chars=250).build([
        make_chunk(1, "A" * 500),
        make_chunk(2, "B" * 500),
    ])

    assert len(context.text) <= 300
    assert len(context.chunks) >= 1
    assert "[Document excerpt truncated for context budget]" in context.text