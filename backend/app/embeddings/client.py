from collections.abc import Sequence
from typing import Protocol

from google import genai
from google.genai import types

from app.core.config import settings

class EmbeddingClient(Protocol):
    """Small interface that keeps the provider replaceable and testable."""
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

def prepare_document(text: str, title: str | None = None) -> str:
    """Apply the retrieval-document format recommended for Embedding 2."""
    return f"title: {title or 'none'} | text: {text}"

class GeminiEmbeddingClient:
    def __init__(self, *, api_key: str | None = None) -> None:
        key = api_key if api_key is not None else settings.gemini_api_key

        if not key:
            raise ValueError("GEMINI_API_KEY is required to generate embeddings.")

        self.client = genai.Client(api_key=key)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        contents = [
            types.Content(parts=[types.Part.from_text(text=text)])
            for text in texts
        ]

        result = self.client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=contents,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.embedding_dimensions,
            ),
        )

        vectors = [list(item.values) for item in result.embeddings]

        if len(vectors) != len(texts):
            raise RuntimeError(
                "Embedding API returned an unexpected number of vectors."
            )

        if any(
            len(vector) != settings.embedding_dimensions
            for vector in vectors
        ):
            raise RuntimeError(
                "Embedding API returned a vector with an unexpected dimension."
            )

        return vectors