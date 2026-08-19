from dataclasses import dataclass

from app.retrieval.models import RerankedChunk

@dataclass(frozen=True)
class BuiltContext:
    """The exact evidence passed to the generation model."""
    text: str
    chunks: tuple[RerankedChunk, ...]

@dataclass(frozen=True)
class GeneratedAnswer:
    """Grounded answer plus the evidence trace used to produce it."""
    answer: str
    context: BuiltContext