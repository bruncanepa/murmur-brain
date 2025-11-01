"""
Health check API controller.

FastAPI routes for health monitoring.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from modules.documents.documents_model import DocumentRepository
from core.dependencies import get_db, get_faiss
from core.database import DatabaseConnection
from core.faiss_manager import FaissIndexManager


router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    stats: Dict[str, Any]


class StatsResponse(BaseModel):
    """Schema for statistics response."""
    success: bool
    stats: Dict[str, int]


def get_document_repository(
    db: DatabaseConnection = Depends(get_db),
    faiss_manager: FaissIndexManager = Depends(get_faiss)
) -> DocumentRepository:
    """Dependency that provides document repository."""
    return DocumentRepository(db, faiss_manager)


@router.get("/health", response_model=HealthResponse)
async def health_check(doc_repo: DocumentRepository = Depends(get_document_repository)):
    """
    Detailed health check.

    Checks database connectivity and returns system statistics.
    """
    try:
        stats = doc_repo.get_stats()
        return HealthResponse(
            status="healthy",
            database="connected",
            stats=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "error": str(e)}
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(doc_repo: DocumentRepository = Depends(get_document_repository)):
    """Get database statistics."""
    try:
        stats = doc_repo.get_stats()
        return StatsResponse(
            success=True,
            stats=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
