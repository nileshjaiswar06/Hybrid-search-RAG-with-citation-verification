from app.generation.models import (
    BuiltContext,
    Citation,
    GeneratedAnswer,
)
from app.retrieval.models import RerankedChunk
from app.verification.models import (
    VerificationDecision,
    VerificationStatus,
)
from app.verification.service import CitationVerificationService


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


class FakeGenerationService:
    def __init__(self, result: GeneratedAnswer) -> None:
        self.result = result

    def answer(self, question, db):
        return self.result


class FakeVerifier:
    def __init__(self, decisions: list[VerificationDecision]) -> None:
        self.decisions = decisions
        self.calls = []

    def verify(self, claim, evidence_excerpt):
        self.calls.append((claim, evidence_excerpt))
        return self.decisions.pop(0)


def test_verification_checks_claim_against_cited_excerpt():
    chunk = make_chunk(
        10,
        "Employees must use passwords with at least twelve characters.",
    )

    generated = GeneratedAnswer(
        answer="Passwords require at least twelve characters. [1]",
        context=BuiltContext(
            text="context",
            chunks=(chunk,),
            excerpts=(
                "Employees must use passwords with at least twelve characters.",
            ),
        ),
        citations=(
            Citation(
                label=1,
                chunk_id=10,
                document_id=1,
                filename="policy.pdf",
                page_number=3,
                chunk_index=10,
            ),
        ),
    )

    verifier = FakeVerifier([
        VerificationDecision(
            status=VerificationStatus.SUPPORTED,
            rationale="The excerpt states the twelve-character requirement.",
        ),
    ])

    service = CitationVerificationService(
        generation_service=FakeGenerationService(generated),
        verifier=verifier,
    )

    result = service.answer(
        "What is the password rule?",
        db=object(),
    )

    assert len(result.verifications) == 1
    assert result.verifications[0].status == VerificationStatus.SUPPORTED
    assert result.verifications[0].citation.label == 1
    assert verifier.calls[0][0] == (
        "Passwords require at least twelve characters."
    )


def test_verification_preserves_insufficient_evidence():
    chunk = make_chunk(
        10,
        "Employees must use passwords with at least twelve characters.",
    )

    generated = GeneratedAnswer(
        answer="Passwords must be changed every 30 days. [1]",
        context=BuiltContext(
            text="context",
            chunks=(chunk,),
            excerpts=(
                "Employees must use passwords with at least twelve characters.",
            ),
        ),
        citations=(
            Citation(
                label=1,
                chunk_id=10,
                document_id=1,
                filename="policy.pdf",
                page_number=3,
                chunk_index=10,
            ),
        ),
    )

    service = CitationVerificationService(
        generation_service=FakeGenerationService(generated),
        verifier=FakeVerifier([
            VerificationDecision(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                rationale=(
                    "The excerpt gives a length requirement but no expiry period."
                ),
            ),
        ]),
    )

    result = service.answer(
        "When must passwords change?",
        db=object(),
    )

    assert (
        result.verifications[0].status
        == VerificationStatus.INSUFFICIENT_EVIDENCE
    )