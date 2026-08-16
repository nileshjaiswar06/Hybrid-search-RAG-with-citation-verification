import pytest

from app.embeddings.client import prepare_document
from app.embeddings.service import EmbeddingService, hash_content

def test_prepare_document_uses_retrieval_structure():
    assert prepare_document("Policy text", "Security Policy") == (
        "title: Security Policy | text: Policy text"
    )

    assert prepare_document("Policy text") == (
        "title: none | text: Policy text"
    )

def test_content_hash_is_stable_and_text_sensitive():
    assert hash_content("same text") == hash_content("same text")
    assert hash_content("same text") != hash_content("different text")

def test_batch_size_must_be_positive():
    with pytest.raises(ValueError):
        EmbeddingService(client=object(), batch_size=0)