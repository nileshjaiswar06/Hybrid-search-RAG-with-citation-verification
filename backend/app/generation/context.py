from collections.abc import Sequence
from html import escape

from app.core.config import settings
from app.generation.models import BuiltContext
from app.retrieval.models import RerankedChunk

class ContextBuilder:
    """Builds a bounded, source-aware context from reranked chunks."""
    def __init__(self, *, max_chars: int | None = None) -> None:
        self.max_chars = (
            settings.generation_context_max_chars
            if max_chars is None
            else max_chars
        )

        if self.max_chars <= 0:
            raise ValueError("max_chars must be positive.")

    def build(self, chunks: Sequence[RerankedChunk]) -> BuiltContext:
        context_parts: list[str] = []
        included_chunks: list[RerankedChunk] = []
        included_excerpts: list[str] = []
        used_chars = 0

        for rank, chunk in enumerate(chunks, start=1):
            header = (
                f'<document citation_id="{rank}" '
                f'rank="{rank}" '
                f'chunk_id="{chunk.chunk_id}" '
                f'source="{escape(chunk.filename)}" '
                f'page="{chunk.page_number}">\n'
            )
            footer = "\n</document>"

            available_for_text = (
                self.max_chars
                - used_chars
                - len(header)
                - len(footer)
            )

            if available_for_text <= 0:
                break

            excerpt = chunk.text.strip()

            if len(excerpt) > available_for_text:
                marker = "\n[Document excerpt truncated for context budget]"
                excerpt = excerpt[: max(0, available_for_text - len(marker))]
                excerpt = excerpt.rstrip() + marker

            part = (
                f"{header}"
                f"{escape(excerpt)}"
                f"{footer}"
            )

            context_parts.append(part)
            included_chunks.append(chunk)
            included_excerpts.append(excerpt)
            used_chars += len(part)

            if used_chars >= self.max_chars:
                break

        return BuiltContext(
            text="\n\n".join(context_parts),
            chunks=tuple(included_chunks),
            excerpts=tuple(included_excerpts)
        )