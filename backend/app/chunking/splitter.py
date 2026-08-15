import re

from app.chunking.models import TextChunk

def split_paragraphs(text: str) -> list[str]:
    paragraphs = re.split(
        r"\n\s*\n",
        text,
    )

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


def split_sentences(text: str) -> list[str]:
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

def prepare_sentences(text: str, max_chars: int) -> list[str]:
    sentences = split_sentences(text)
    result = []

    for sentence in sentences:
        if len(sentence) <= max_chars:
            result.append(sentence)
            continue

        for i in range(0, len(sentence), max_chars):
            result.append(
                sentence[i:i + max_chars]
            )

    return result

def build_chunk(
    sentences: list[str],
    start_char: int,
    end_char: int,
    chunk_index: int,
) -> TextChunk:

    return TextChunk(
        text=" ".join(sentences).strip(),
        chunk_index=chunk_index,
        start_char=start_char,
        end_char=end_char,
    )

class TextChunker:
    def __init__( self, target_chars: int = 2800, overlap_chars: int = 400 ):
        if target_chars <= 0:
            raise ValueError(
                "target_chars must be positive"
            )

        if overlap_chars < 0:
            raise ValueError(
                "overlap_chars cannot be negative"
            )

        if overlap_chars >= target_chars:
            raise ValueError(
                "overlap_chars must be smaller than target_chars"
            )

        self.target_chars = target_chars
        self.overlap_chars = overlap_chars

    def chunk( self, text: str ) -> list[TextChunk]:

        if not text.strip():
            return []

        paragraphs = split_paragraphs(text)
        chunks: list[TextChunk] = []

        current_sentences: list[str] = []
        current_length = 0
        chunk_index = 0
        global_position = 0

        for paragraph in paragraphs:
            sentences = prepare_sentences(paragraph, self.target_chars)

            for sentence in sentences:
                sentence_length = len(sentence)

                if (
                    current_sentences
                    and
                    current_length + sentence_length
                    > self.target_chars
                ):
                    chunk = build_chunk(
                        current_sentences,
                        global_position - current_length,
                        global_position,
                        chunk_index,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    overlap_sentences = []
                    overlap_length = 0

                    for previous in reversed(current_sentences):
                        if (
                            overlap_length
                            + len(previous)
                            > self.overlap_chars
                        ):
                            break

                        overlap_sentences.insert(0, previous)
                        overlap_length += (len(previous))

                    current_sentences = (overlap_sentences)
                    current_length = (overlap_length)

                current_sentences.append(sentence)
                current_length += (sentence_length + 1)
                global_position += (sentence_length + 1)

        if current_sentences:
            chunks.append(
                build_chunk(
                    current_sentences,
                    global_position - current_length,
                    global_position,
                    chunk_index,
                )
            )

        return chunks
