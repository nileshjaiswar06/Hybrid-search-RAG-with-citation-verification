from math import log2
from statistics import mean

def _unique_top_k(retrieved_chunk_ids: list[int], k: int) -> list[int]:
    if k <= 0:
        raise ValueError("k must be positive.")

    result: list[int] = []
    seen: set[int] = set()

    for chunk_id in retrieved_chunk_ids:
        if chunk_id not in seen:
            result.append(chunk_id)
            seen.add(chunk_id)

        if len(result) == k:
            break

    return result

def precision_at_k(retrieved_chunk_ids: list[int], relevant_chunk_ids: set[int], k: int) -> float:
    retrieved = _unique_top_k(retrieved_chunk_ids, k)

    hits = sum(
        chunk_id in relevant_chunk_ids
        for chunk_id in retrieved
    )

    return hits / k

def recall_at_k(retrieved_chunk_ids: list[int], relevant_chunk_ids: set[int], k: int) -> float:
    if not relevant_chunk_ids:
        raise ValueError(
            "Recall requires at least one relevant chunk."
        )

    retrieved = _unique_top_k(retrieved_chunk_ids, k)

    hits = sum(
        chunk_id in relevant_chunk_ids
        for chunk_id in retrieved
    )

    return hits / len(relevant_chunk_ids)

def reciprocal_rank(retrieved_chunk_ids: list[int], relevant_chunk_ids: set[int], k: int) -> float:
    retrieved = _unique_top_k(retrieved_chunk_ids, k)

    for rank, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant_chunk_ids:
            return 1 / rank

    return 0.0

def ndcg_at_k(retrieved_chunk_ids: list[int], relevant_chunk_ids: set[int], k: int) -> float:
    retrieved = _unique_top_k(retrieved_chunk_ids, k)

    dcg = sum(
        1 / log2(rank + 1)
        for rank, chunk_id in enumerate(retrieved, start=1)
        if chunk_id in relevant_chunk_ids
    )

    ideal_relevant_count = min(
        len(relevant_chunk_ids),
        k,
    )

    if ideal_relevant_count == 0:
        return 0.0

    ideal_dcg = sum(
        1 / log2(rank + 1)
        for rank in range(1, ideal_relevant_count + 1)
    )

    return dcg / ideal_dcg

def evaluate_retrieval(retrieved_chunk_ids: list[int], relevant_chunk_ids: set[int], k: int) -> dict[str, float]:
    return {
        f"precision_at_{k}": precision_at_k(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k,
        ),
        f"recall_at_{k}": recall_at_k(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k,
        ),
        f"mrr_at_{k}": reciprocal_rank(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k,
        ),
        f"ndcg_at_{k}": ndcg_at_k(
            retrieved_chunk_ids,
            relevant_chunk_ids,
            k,
        ),
    }


def mean_metrics(metric_rows: list[dict[str, float]]) -> dict[str, float]:
    if not metric_rows:
        return {}

    return {
        metric_name: mean(
            row[metric_name]
            for row in metric_rows
        )
        for metric_name in metric_rows[0]
    }