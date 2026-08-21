import argparse

from app.db.database import SessionLocal
from app.verification.service import CitationVerificationService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a question and verify every cited claim."
    )

    parser.add_argument(
        "question",
        help="Question to answer from indexed documents.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        result = CitationVerificationService().answer(
            args.question,
            db,
        )

        generated = result.generated_answer

        print("\nAnswer:")
        print(generated.answer)

        print("\nCitations:")

        if not generated.citations:
            print("No citations.")

        for citation in generated.citations:
            print(
                f"[{citation.label}] "
                f"{citation.filename}, "
                f"page {citation.page_number}, "
                f"chunk {citation.chunk_id}"
            )

        print("\nCitation verification:")

        if not result.verifications:
            print("No cited claims to verify.")

        for item in result.verifications:
            print(
                f"\n{item.status.value} | "
                f"Citation [{item.citation.label}]"
            )
            print(f"Claim: {item.claim}")
            print(f"Reason: {item.rationale}")

    finally:
        db.close()

if __name__ == "__main__":
    main()