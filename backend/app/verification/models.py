from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from app.generation.models import Citation, GeneratedAnswer

class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class VerificationDecision(BaseModel):
    """Structured response produced by the verification model."""
    status: VerificationStatus
    rationale: str = Field(min_length=1, max_length=500)

@dataclass(frozen=True)
class CitedClaim:
    """One answer fragment followed by one or more citation labels."""
    text: str
    citation_labels: tuple[int, ...]

@dataclass(frozen=True)
class ClaimCitationVerification:
    """Verification result for one claim against one cited source."""
    claim: str
    citation: Citation
    evidence_excerpt: str
    status: VerificationStatus
    rationale: str

@dataclass(frozen=True)
class VerificationResult:
    """Generated answer plus claim-level citation verification results."""
    generated_answer: GeneratedAnswer
    verifications: tuple[ClaimCitationVerification, ...]