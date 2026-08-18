import argparse

from app.db.database import SessionLocal
from app.retrieval.hybrid import HybridRetrievalService

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search document chunks using dense + BM25 hybrid retrieval."
    )

    parser.add_argument(
        "query",
        help="Natural-language search query.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of final results to return. Default: 5.",
    )

    parser.add_argument(
        "--candidate-k",
        type=int,
        default=20,
        help="Candidates retrieved from each retriever. Default: 20.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        results = HybridRetrievalService().search(
            args.query,
            db,
            top_k=args.top_k,
            candidate_k=args.candidate_k,
        )

        if not results:
            print("No hybrid retrieval results were found.")
            return

        for rank, result in enumerate(results, start=1):
            preview = result.text.replace("\n", " ").strip()

            print(f"\nRank: {rank}")
            print(f"RRF score: {result.rrf_score:.6f}")
            print(f"Dense rank: {result.dense_rank}")
            print(f"BM25 rank: {result.bm25_rank}")
            print(
                "Retrieved by: "
                + ", ".join(result.retrieved_by)
            )
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