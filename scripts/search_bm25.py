import argparse

from app.db.database import SessionLocal
from app.retrieval.bm25 import BM25RetrievalService

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search document chunks using BM25."
    )

    parser.add_argument(
        "query",
        help="Keyword or natural-language search query.",
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
        service = BM25RetrievalService()

        indexed_count = service.build_index(db)
        print(f"BM25 index built from {indexed_count} chunks.")

        results = service.search(
            args.query,
            top_k=args.top_k,
        )

        if not results:
            print("No lexical matches were found.")
            return

        for rank, result in enumerate(results, start=1):
            preview = result.text.replace("\n", " ").strip()

            print(f"\nRank: {rank}")
            print(f"BM25 score: {result.score:.4f}")
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