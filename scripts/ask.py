import argparse

from app.db.database import SessionLocal
from app.generation.service import GenerationService

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a grounded question about indexed documents."
    )

    parser.add_argument(
        "question",
        help="Question to answer from the indexed documents.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        result = GenerationService().answer(
            args.question,
            db,
        )

        print("\nAnswer:")
        print(result.answer)

        print("\nCitations:")

        if not result.citations:
            print("No citations.")

        for citation in result.citations:
            print(
                f"[{citation.label}] "
                f"{citation.filename}, "
                f"page {citation.page_number}, "
                f"chunk {citation.chunk_id}"
            )

        if not result.context.chunks:
            print("No retrieved chunks.")

    finally:
        db.close()

if __name__ == "__main__":
    main()