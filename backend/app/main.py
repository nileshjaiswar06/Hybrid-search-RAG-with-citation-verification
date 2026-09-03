from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Hybrid Search RAG with Citation Verification",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(rag_router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.1.0",
    }