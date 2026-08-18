from dataclasses import dataclass

@dataclass(frozen=True)
class RetrievedChunk:
    """One dense-retrieval result with its source trace."""
    chunk_id: int
    document_id: int
    filename: str
    page_number: int
    chunk_index: int
    text: str
    score: float

@dataclass(frozen=True)
class HybridRetrievedChunk:
    """One result produced by dense + BM25 rank fusion."""
    chunk_id: int
    document_id: int
    filename: str
    page_number: int
    chunk_index: int
    text: str
    rrf_score: float
    dense_rank: int | None
    bm25_rank: int | None
    retrieved_by: tuple[str, ...]