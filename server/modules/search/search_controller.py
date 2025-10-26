"""
Search API controller.

FastAPI routes for semantic vector search.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from .search_model import VectorRepository, SearchResponse
from .search_service import SearchService
from core.dependencies import get_db, get_ollama
from core.database import DatabaseConnection
from core.ollama_client import OllamaClient


router = APIRouter(prefix="/api/search", tags=["search"])


def get_vector_repository(db: DatabaseConnection = Depends(get_db)) -> VectorRepository:
    """Dependency that provides vector repository."""
    return VectorRepository(db)


def get_search_service(
    vector_repo: VectorRepository = Depends(get_vector_repository),
    ollama: OllamaClient = Depends(get_ollama)
) -> SearchService:
    """Dependency that provides search service."""
    return SearchService(vector_repo, ollama)


@router.get("", response_model=SearchResponse)
async def search_vectors(
    query: str = Query(..., description="Search query text"),
    top_k: int = Query(5, ge=1, le=100, description="Number of top results to return"),
    threshold: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score"),
    doc_ids: Optional[str] = Query(None, description="Comma-separated list of document IDs to filter by"),
    service: SearchService = Depends(get_search_service)
):
    """
    Perform semantic search over document chunks.

    Returns search results with similarity scores and document metadata.
    """
    try:
        # Parse doc_ids from comma-separated string to list
        parsed_doc_ids = None
        if doc_ids:
            parsed_doc_ids = [id.strip() for id in doc_ids.split(',') if id.strip()]

        result = service.search(
            query=query.strip(),
            top_k=top_k,
            threshold=threshold,
            doc_ids=parsed_doc_ids
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
