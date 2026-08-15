import pytest

from app.chunking.splitter import (TextChunker, split_paragraphs, split_sentences)

def test_split_paragraphs():
    text = (
        "First paragraph.\n\n"
        "Second paragraph."
    )

    result = split_paragraphs(text)

    assert result == [
        "First paragraph.",
        "Second paragraph.",
    ]

def test_split_sentences():
    text = (
        "This is sentence one. "
        "This is sentence two. "
        "Is this sentence three?"
    )

    result = split_sentences(text)

    assert result == [
        "This is sentence one.",
        "This is sentence two.",
        "Is this sentence three?",
    ]

def test_chunking():
    text = (
        "Sentence one. "
        "Sentence two. "
        "Sentence three. "
        "Sentence four."
    )

    chunker = TextChunker(target_chars=35, overlap_chars=10)

    chunks = chunker.chunk(text)

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.text
        assert chunk.end_char >= chunk.start_char

def test_empty_text():
    chunker = TextChunker()

    assert chunker.chunk("") == []
    assert chunker.chunk("   ") == []

def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        TextChunker(target_chars=0)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        TextChunker(target_chars=100, overlap_chars=100)

def test_long_sentence():
    text = "A" * 5000

    chunker = TextChunker(target_chars=1000, overlap_chars=100)

    chunks = chunker.chunk(text)

    assert len(chunks) >= 5

    for chunk in chunks:
        assert len(chunk.text) <= 1000