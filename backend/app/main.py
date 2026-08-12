from fastapi import FastAPI
from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Hybrid Search RAG with Citation Verification",
)

app.include_router(health_router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "0.1.0",
    }