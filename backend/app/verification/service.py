from sqlalchemy.orm import Session

from app.generation.service import GenerationService, NO_ANSWER
from app.verification.client import CitationVerifier, GeminiCitationVerifier
from app.verification.models import (ClaimCitationVerification, VerificationResult)
from app.verification.parsing import extract_cited_claims

class CitationVerificationService:
    """Generates a cited answer and verifies each cited claim."""
    def __init__(self, *, generation_service: GenerationService | None = None, verifier: CitationVerifier | None = None) -> None:
        self.generation_service = (
            generation_service
            or GenerationService()
        )
        self.verifier = verifier or GeminiCitationVerifier()

    def answer(self, question: str, db: Session) -> VerificationResult:
        generated = self.generation_service.answer(
            question,
            db,
        )

        if generated.answer == NO_ANSWER:
            return VerificationResult(
                generated_answer=generated,
                verifications=(),
            )

        if len(generated.context.chunks) != len(
            generated.context.excerpts
        ):
            raise RuntimeError(
                "Context chunks and excerpts must have matching lengths."
            )

        citation_by_label = {
            citation.label: citation
            for citation in generated.citations
        }

        excerpt_by_label = {
            label: excerpt
            for label, excerpt in enumerate(
                generated.context.excerpts,
                start=1,
            )
        }

        cited_claims = extract_cited_claims(
            generated.answer
        )

        if not cited_claims:
            raise RuntimeError(
                "Generated answer has citations but no verifiable cited claims."
            )

        verifications: list[ClaimCitationVerification] = []

        for cited_claim in cited_claims:
            for label in cited_claim.citation_labels:
                citation = citation_by_label.get(label)
                evidence_excerpt = excerpt_by_label.get(label)

                if citation is None or evidence_excerpt is None:
                    raise RuntimeError(
                        f"Citation [{label}] cannot be verified."
                    )

                decision = self.verifier.verify(
                    cited_claim.text,
                    evidence_excerpt,
                )

                verifications.append(
                    ClaimCitationVerification(
                        claim=cited_claim.text,
                        citation=citation,
                        evidence_excerpt=evidence_excerpt,
                        status=decision.status,
                        rationale=decision.rationale,
                    )
                )

        return VerificationResult(
            generated_answer=generated,
            verifications=tuple(verifications),
        )