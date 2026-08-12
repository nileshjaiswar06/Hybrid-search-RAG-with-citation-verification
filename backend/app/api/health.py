from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.db.database import get_db

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

@router.get("")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "service": "hybrid-rag-api",
        "database": "connected",
    }