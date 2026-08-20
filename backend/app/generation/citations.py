import re

from app.generation.models import BuiltContext, Citation

CITATION_PATTERN = re.compile(r"\[(\d+)\]")

def build_citation_catalog(context: BuiltContext) -> dict[int, Citation]:
    """Map each context position to its real source metadata."""
    return {
        label: Citation(
            label=label,
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            filename=chunk.filename,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
        )
        for label, chunk in enumerate(context.chunks, start=1)
    }

def resolve_citations(answer: str, context: BuiltContext, *, require_citations: bool) -> tuple[Citation, ...]:
    """Extract answer citations and validate them against supplied context."""
    catalog = build_citation_catalog(context)

    labels_in_order = [
        int(label)
        for label in CITATION_PATTERN.findall(answer)
    ]

    if require_citations and not labels_in_order:
        raise RuntimeError(
            "Generated answer contains no citations."
        )

    unknown_labels = sorted(
        set(labels_in_order) - set(catalog)
    )

    if unknown_labels:
        raise RuntimeError(
            "Generated answer contains citation IDs not present in context: "
            + ", ".join(f"[{label}]" for label in unknown_labels)
        )

    unique_labels = list(dict.fromkeys(labels_in_order))

    return tuple(
        catalog[label]
        for label in unique_labels
    )