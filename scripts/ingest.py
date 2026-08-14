import sys
from pathlib import Path

from app.db.database import SessionLocal
from app.ingestion.service import IngestionService

def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/ingest.py <pdf_path>"
        )
        raise SystemExit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(
            f"File not found: {file_path}"
        )
        raise SystemExit(1)

    db = SessionLocal()

    try:
        service = IngestionService()

        document = service.ingest_and_persist(
            file_path,
            db,
        )

        print("Document ingested successfully.")
        print(f"ID: {document.id}")
        print(f"Filename: {document.filename}")
        print(f"Pages: {document.page_count}")
        print(f"Hash: {document.file_hash}")

    finally:
        db.close()


if __name__ == "__main__":
    main()