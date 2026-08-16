import pytest

from app.embeddings.client import prepare_query
from app.retrieval.service import DenseRetrievalService

def test_prepare_query_uses_search_format():
    assert prepare_query("What is the password policy?") == (
        "task: search result | query: What is the password policy?"
    )

def test_prepare_query_rejects_blank_query():
    with pytest.raises(ValueError, match="Query cannot be empty"):
        prepare_query("   ")

def test_search_rejects_blank_query_before_accessing_database():
    service = DenseRetrievalService(client=object())

    with pytest.raises(ValueError, match="Query cannot be empty"):
        service.search("   ", db=object())

def test_search_rejects_non_positive_top_k():
    service = DenseRetrievalService(client=object())

    with pytest.raises(ValueError, match="top_k must be positive"):
        service.search("password policy", db=object(), top_k=0)