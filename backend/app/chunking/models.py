from dataclasses import dataclass, field


@dataclass
class TextChunk:
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)