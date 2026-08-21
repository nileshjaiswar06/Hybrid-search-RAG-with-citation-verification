import pytest

from app.evaluation.metrics import (
    evaluate_retrieval,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_retrieval_metrics_for_perfect_ranking():
    retrieved = [10, 20, 30]
    relevant = {10, 20}

    assert precision_at_k(retrieved, relevant, 3) == pytest.approx(
        2 / 3
    )
    assert recall_at_k(retrieved, relevant, 3) == 1.0
    assert reciprocal_rank(retrieved, relevant, 3) == 1.0
    assert ndcg_at_k(retrieved, relevant, 3) == 1.0


def test_retrieval_metrics_when_relevant_result_is_late():
    retrieved = [30, 20, 10]
    relevant = {10}

    metrics = evaluate_retrieval(
        retrieved,
        relevant,
        k=3,
    )

    assert metrics["precision_at_3"] == pytest.approx(
        1 / 3
    )
    assert metrics["recall_at_3"] == 1.0
    assert metrics["mrr_at_3"] == pytest.approx(
        1 / 3
    )
    assert metrics["ndcg_at_3"] < 1.0


def test_retrieval_metrics_when_no_result_is_relevant():
    retrieved = [1, 2, 3]
    relevant = {10}

    assert precision_at_k(retrieved, relevant, 3) == 0.0
    assert recall_at_k(retrieved, relevant, 3) == 0.0
    assert reciprocal_rank(retrieved, relevant, 3) == 0.0
    assert ndcg_at_k(retrieved, relevant, 3) == 0.0