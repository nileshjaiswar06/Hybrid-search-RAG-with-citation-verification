from collections.abc import Sequence
from typing import Protocol

from app.core.config import settings

class Reranker(Protocol):
    """Interface for any query-passage reranking model."""
    def score(self, query: str, passages: Sequence[str]) -> list[float]: ...

class CrossEncoderReranker:
    """Local cross-encoder relevance scorer."""
    def __init__(self, *, model_name: str | None = None, batch_size: int | None = None, max_length: int | None = None) -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as error:
            raise RuntimeError(
                "sentence-transformers is required for reranking. "
                "Run: pip install -r requirements.txt"
            ) from error

        self.model_name = model_name or settings.reranker_model
        self.batch_size = (
            settings.reranker_batch_size
            if batch_size is None
            else batch_size
        )
        self.max_length = (
            settings.reranker_max_length
            if max_length is None
            else max_length
        )

        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive.")

        if self.max_length <= 0:
            raise ValueError("max_length must be positive.")

        self.model = CrossEncoder(
            self.model_name,
            max_length=self.max_length,
        )

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError("Query cannot be empty.")

        if not passages:
            return []

        pairs = [
            (cleaned_query, passage)
            for passage in passages
        ]

        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        values = [float(score) for score in scores]

        if len(values) != len(passages):
            raise RuntimeError(
                "Reranker returned an unexpected number of scores."
            )

        return values