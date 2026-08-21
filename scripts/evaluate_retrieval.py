import argparse
import json
from pathlib import Path
from time import perf_counter

from app.db.database import SessionLocal
from app.evaluation.dataset import load_evaluation_cases
from app.evaluation.metrics import (
    evaluate_retrieval,
    mean_metrics,
)
from app.reranking.service import RerankingService
from app.retrieval.bm25 import BM25RetrievalService
from app.retrieval.hybrid import HybridRetrievalService
from app.retrieval.service import DenseRetrievalService


def run_system(
    *,
    system_name: str,
    cases,
    search,
    k: int,
) -> dict:
    query_reports = []
    metric_rows = []

    for case in cases:
        started_at = perf_counter()
        results = search(case.question)
        latency_ms = (perf_counter() - started_at) * 1000

        retrieved_ids = [
            result.chunk_id
            for result in results
        ]

        metrics = evaluate_retrieval(
            retrieved_ids,
            set(case.relevant_chunk_ids),
            k,
        )

        metric_rows.append(metrics)

        query_reports.append({
            "case_id": case.id,
            "question": case.question,
            "relevant_chunk_ids": case.relevant_chunk_ids,
            "retrieved_chunk_ids": retrieved_ids,
            "latency_ms": round(latency_ms, 2),
            **metrics,
        })

    summary = mean_metrics(metric_rows)

    summary["average_latency_ms"] = round(
        sum(
            report["latency_ms"]
            for report in query_reports
        ) / len(query_reports),
        2,
    )

    return {
        "system": system_name,
        "summary": summary,
        "queries": query_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval systems against labeled chunk IDs."
    )

    parser.add_argument(
        "--dataset",
        default="evaluation/data/retrieval_cases.json",
        help="Path to evaluation dataset JSON.",
    )

    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Top-K value for all retrievers. Default: 5.",
    )

    parser.add_argument(
        "--systems",
        nargs="+",
        choices=["dense", "bm25", "hybrid", "reranked"],
        default=["dense", "bm25", "hybrid", "reranked"],
        help="Retrieval systems to evaluate.",
    )

    parser.add_argument(
        "--output",
        default="evaluation/results/retrieval_report.json",
        help="Output JSON report path.",
    )

    args = parser.parse_args()

    if args.k <= 0:
        raise ValueError("k must be positive.")

    cases = load_evaluation_cases(args.dataset)

    answerable_cases = [
        case
        for case in cases
        if case.answerable
    ]

    if not answerable_cases:
        raise ValueError(
            "Dataset must include at least one answerable case."
        )

    db = SessionLocal()

    try:
        dense = DenseRetrievalService()

        bm25 = BM25RetrievalService()
        bm25.build_index(db)

        hybrid = HybridRetrievalService()

        reranked = RerankingService()

        systems = {
            "dense": lambda question: dense.search(
                question,
                db,
                top_k=args.k,
            ),
            "bm25": lambda question: bm25.search(
                question,
                top_k=args.k,
            ),
            "hybrid": lambda question: hybrid.search(
                question,
                db,
                top_k=args.k,
            ),
            "reranked": lambda question: reranked.search(
                question,
                db,
                top_k=args.k,
            ),
        }

        reports = {
            system_name: run_system(
                system_name=system_name,
                cases=answerable_cases,
                search=systems[system_name],
                k=args.k,
            )
            for system_name in args.systems
        }

    finally:
        db.close()

    report = {
        "dataset_size": len(cases),
        "answerable_case_count": len(answerable_cases),
        "top_k": args.k,
        "systems": reports,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"Retrieval report saved to: {output_path}")

    for system_name, system_report in reports.items():
        print(f"\n{system_name.upper()}")
        for metric, value in system_report["summary"].items():
            print(f"{metric}: {value}")


if __name__ == "__main__":
    main()