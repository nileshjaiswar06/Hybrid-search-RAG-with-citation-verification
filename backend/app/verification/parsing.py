import re

from app.verification.models import CitedClaim

CITATION_GROUP_PATTERN = re.compile(
    r"(?P<citations>(?:\[\d+\])+)"
)

def extract_cited_claims(answer: str) -> list[CitedClaim]:
    """
    Extract the text immediately before each citation group.

    Phase 9 requires citations immediately after factual claims, so this
    parser treats that preceding text as the cited claim.
    """

    claims: list[CitedClaim] = []
    cursor = 0

    for match in CITATION_GROUP_PATTERN.finditer(answer):
        claim_text = answer[cursor:match.start()].strip()

        labels = tuple(
            int(label)
            for label in re.findall(
                r"\[(\d+)\]",
                match.group("citations"),
            )
        )

        if claim_text and labels:
            claims.append(
                CitedClaim(
                    text=claim_text,
                    citation_labels=labels,
                )
            )

        cursor = match.end()
    return claims