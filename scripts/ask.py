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

        print("\nRetrieved context trace (debug only):")

        if not result.context.chunks:
            print("No retrieved chunks.")

        for rank, chunk in enumerate(result.context.chunks, start=1):
            print(
                f"{rank}. {chunk.filename} | "
                f"page {chunk.page_number} | "
                f"chunk {chunk.chunk_id}"
            )

    finally:
        db.close()

if __name__ == "__main__":
    main()