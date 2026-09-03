import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Document
from app.embeddings.service import EmbeddingService
from app.ingestion.service import IngestionService
from app.verification.service import CitationVerificationService


router = APIRouter(
    prefix="/api",
    tags=["RAG"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"


class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
    )


@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
):
    documents = db.scalars(
        select(Document).order_by(Document.created_at.desc())
    ).all()

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "title": document.title,
            "page_count": document.page_count,
        }
        for document in documents
    ]


@router.post("/documents/upload")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A PDF file is required.",
        )

    safe_filename = Path(file.filename).name

    if Path(safe_filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    saved_path = (
        DOCUMENTS_DIR
        / f"{uuid4().hex[:8]}_{safe_filename}"
    )

    try:
        with saved_path.open("wb") as output_file:
            shutil.copyfileobj(
                file.file,
                output_file,
            )

        ingestion_service = IngestionService()

        document = ingestion_service.ingest_and_persist(
            saved_path,
            db,
        )

        embedded_chunks = EmbeddingService().embed_document(
            document.id,
            db,
        )

        return {
            "id": document.id,
            "filename": document.filename,
            "page_count": document.page_count,
            "embedded_chunks": embedded_chunks,
            "message": "Document is indexed and ready for questions.",
        }

    except Exception as error:
        db.rollback()

        if saved_path.exists():
            saved_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {error}",
        ) from error

    finally:
        file.file.close()


@router.post("/ask")
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    try:
        result = CitationVerificationService().answer(
            request.question,
            db,
        )

        generated = result.generated_answer

        return {
            "answer": generated.answer,
            "citations": [
                {
                    "label": citation.label,
                    "filename": citation.filename,
                    "page_number": citation.page_number,
                    "chunk_id": citation.chunk_id,
                }
                for citation in generated.citations
            ],
            "verification": [
                {
                    "claim": item.claim,
                    "status": item.status.value,
                    "rationale": item.rationale,
                    "citation_label": item.citation.label,
                }
                for item in result.verifications
            ],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Question processing failed: {error}",
        ) from error