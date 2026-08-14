from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PageContent:
    page_number: int
    text: str
    metadata: dict = field(default_factory=dict)

@dataclass
class ParsedDocument:
    filename: str
    file_path: str
    title: str | None
    author: str | None
    subject: str | None
    page_count: int
    file_size: int
    file_hash: str
    created_at: datetime
    pages: list[PageContent]

@dataclass
class IngestionStats:
    page_count: int
    non_empty_pages: int
    empty_pages: int
    character_count: int