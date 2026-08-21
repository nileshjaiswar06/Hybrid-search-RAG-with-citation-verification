import argparse
import json
from collections import Counter
from pathlib import Path

from app.db.database import SessionLocal
from app.evaluation.dataset import load_evaluation_cases
from app.generation.service import NO_ANSWER
from app.verification.service import CitationVerificationService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate answers, abstention, and citation support."
    )

    parser.add_argument(
        "--dataset",
        default="evaluation/data/retrieval_cases.json",
        help="Path to evaluation dataset JSON.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of cases to run.",
    )

    parser.add_argument(
        "--output",
        default="evaluation/results/answer_report.json",
        help="Output JSON report path.",
    )

    args = parser.parse_args()

    cases = load_evaluation_cases(args.dataset)

    if args.limit is not None:
        cases = cases[:args.limit]

    db = SessionLocal()

    try:
        service = CitationVerificationService()

        reports = []

        for case in cases:
          try:
            result = service.answer(
                case.question,
                db,
            )
            generated = result.generated_answer

            abstained = generated.answer == NO_ANSWER
            abstention_correct = (abstained == (not case.answerable))

            reports.append({
                "case_id": case.id,
                "question": case.question,
                "answerable": case.answerable,
                "answer": generated.answer,
                "citation_count": len(generated.citations),
                "abstained": abstained,
                "abstention_correct": abstention_correct,
                "verifications": [
                    {
                        "claim": item.claim,
                        "citation_label": item.citation.label,
                        "source": item.citation.filename,
                        "page_number": item.citation.page_number,
                        "chunk_id": item.citation.chunk_id,
                        "status": item.status.value,
                        "rationale": item.rationale,
                    }
                    for item in result.verifications
                ],
            })

          except RuntimeError as e:
              # Handle uncited answers gracefully
              print(f"Case {case.id} failed due to citation error: {e}")
              reports.append({
                  "case_id": case.id,
                  "question": case.question,
                  "answerable": case.answerable,
                  "answer": NO_ANSWER,
                  "citation_count": 0,
                  "abstained": True,
                  "abstention_correct": not case.answerable,
                  "verifications": [],
              })

    finally:
        db.close()

    status_counts = Counter(
        verification["status"]
        for report in reports
        for verification in report["verifications"]
    )

    verification_count = sum(
        status_counts.values()
    )

    supported_count = status_counts["SUPPORTED"]

    report = {
        "case_count": len(reports),
        "abstention_accuracy": (
            sum(
                item["abstention_correct"]
                for item in reports
            ) / len(reports)
            if reports else 0.0
        ),
        "automated_citation_support_rate": (
            supported_count / verification_count
            if verification_count else 0.0
        ),
        "verification_status_counts": dict(status_counts),
        "cases": reports,
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

    print(f"Answer report saved to: {output_path}")
    print(
        "Abstention accuracy: "
        f"{report['abstention_accuracy']:.3f}"
    )
    print(
        "Automated citation support rate: "
        f"{report['automated_citation_support_rate']:.3f}"
    )


if __name__ == "__main__":
    main()