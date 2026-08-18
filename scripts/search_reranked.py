import argparse

from app.db.database import SessionLocal
from app.reranking.service import RerankingService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search and rerank document chunks."
    )

    parser.add_argument(
        "query",
        help="Natural-language search query.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Final number of reranked chunks. Default: 5.",
    )

    parser.add_argument(
        "--candidate-k",
        type=int,
        default=20,
        help="Hybrid candidates to rerank. Default: 20.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        results = RerankingService().search(
            args.query,
            db,
            top_k=args.top_k,
            candidate_k=args.candidate_k,
        )

        if not results:
            print("No reranked results were found.")
            return

        for final_rank, result in enumerate(results, start=1):
            preview = result.text.replace("\n", " ").strip()

            print(f"\nFinal rank: {final_rank}")
            print(f"Reranker score: {result.reranker_score:.4f}")
            print(f"Previous hybrid rank: {result.hybrid_rank}")
            print(f"RRF score: {result.rrf_score:.6f}")
            print(f"Dense rank: {result.dense_rank}")
            print(f"BM25 rank: {result.bm25_rank}")
            print("Retrieved by: " + ", ".join(result.retrieved_by))
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