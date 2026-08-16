import argparse

from app.db.database import SessionLocal
from app.retrieval.service import DenseRetrievalService

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search document chunks using dense retrieval."
    )

    parser.add_argument(
        "query",
        help="Natural-language search question.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to return. Default: 5.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        results = DenseRetrievalService().search(
            args.query,
            db,
            top_k=args.top_k,
        )

        if not results:
            print("No embedded chunks were found.")
            return

        for rank, result in enumerate(results, start=1):
            preview = result.text.replace("\n", " ").strip()

            print(f"\nRank: {rank}")
            print(f"Score: {result.score:.4f}")
            print(
                f"Source: {result.filename} | "
                f"Page: {result.page_number} | "
                f"Chunk: {result.chunk_index}"
            )
            print(f"Chunk ID: {result.chunk_id}")
            print(f"Text: {preview[:500]}")

    finally:
        db.close()

if __name__ == "__main__":
    main()