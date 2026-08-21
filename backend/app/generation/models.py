from dataclasses import dataclass

from app.retrieval.models import RerankedChunk

@dataclass(frozen=True)
class BuiltContext:
    """The exact evidence passed to the generation model."""
    text: str
    chunks: tuple[RerankedChunk, ...]
    excerpts: tuple[str, ...] = ()

@dataclass(frozen=True)
class Citation:
    """A validated citation mapped to a real context chunk."""
    label: int
    chunk_id: int
    document_id: int
    filename: str
    page_number: int
    chunk_index: int

@dataclass(frozen=True)
class GeneratedAnswer:
    """Grounded answer, source context, and validated citations."""
    answer: str
    context: BuiltContext
    citations: tuple[Citation, ...] = ()