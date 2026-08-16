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