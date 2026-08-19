import pytest

from app.generation.context import ContextBuilder
from app.generation.service import GenerationService, NO_ANSWER
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

class FakeRerankingService:
    def __init__(self, chunks: list[RerankedChunk]) -> None:
        self.chunks = chunks

    def search(self, question, db, *, top_k, candidate_k):
        return self.chunks[:top_k]

class FakeGenerator:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer

def test_generation_uses_context_and_returns_answer():
    generator = FakeGenerator("Employees need strong passwords.")

    service = GenerationService(
        reranking_service=FakeRerankingService([
            make_chunk(1, "Employees must use strong passwords."),
        ]),
        context_builder=ContextBuilder(max_chars=1000),
        generator=generator,
    )

    result = service.answer(
        "What is the password rule?",
        db=object(),
    )

    assert result.answer == "Employees need strong passwords."
    assert len(result.context.chunks) == 1
    assert "What is the password rule?" in generator.prompts[0]
    assert "Employees must use strong passwords." in generator.prompts[0]

def test_generation_returns_no_answer_without_context():
    generator = FakeGenerator("This should not be used.")

    service = GenerationService(
        reranking_service=FakeRerankingService([]),
        context_builder=ContextBuilder(max_chars=1000),
        generator=generator,
    )

    result = service.answer(
        "What is the leave policy?",
        db=object(),
    )

    assert result.answer == NO_ANSWER
    assert result.context.chunks == ()
    assert generator.prompts == []

def test_generation_rejects_blank_question():
    service = GenerationService(
        reranking_service=FakeRerankingService([]),
        context_builder=ContextBuilder(max_chars=1000),
        generator=FakeGenerator("Unused"),
    )

    with pytest.raises(ValueError, match="Question cannot be empty"):
        service.answer("   ", db=object())