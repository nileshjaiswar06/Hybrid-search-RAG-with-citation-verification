import sys

from app.db.database import SessionLocal
from app.embeddings.service import EmbeddingService

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/embed.py <document_id>")
        raise SystemExit(1)

    try:
        document_id = int(sys.argv[1])
    except ValueError:
        print("document_id must be an integer")
        raise SystemExit(1)

    db = SessionLocal()

    try:
        created = EmbeddingService().embed_document(document_id, db)
        print(f"Embedding completed: {created} chunks generated or refreshed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()