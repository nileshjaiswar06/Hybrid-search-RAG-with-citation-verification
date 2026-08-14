from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document

class DocumentRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_hash( self, file_hash: str ) -> Document | None:
        statement = select(Document).where(
            Document.file_hash == file_hash
        )

        return self.db.scalar(statement)

    def create( self, document: Document ) -> Document:
        self.db.add(document)
        self.db.flush()

        return document

    def save(self) -> None:
        self.db.commit()