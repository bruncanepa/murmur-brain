"""
Ollama API controller.

FastAPI routes for Ollama integration.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from .ollama_model import OllamaStatusResponse, ModelSearchResponse, CategoryResponse, ChatModelsResponse
from .ollama_service import OllamaService
from core.dependencies import get_ollama
from core.ollama_client import OllamaClient


router = APIRouter(prefix="/api/ollama", tags=["ollama"])


def get_ollama_service(ollama: OllamaClient = Depends(get_ollama)) -> OllamaService:
    """Dependency that provides Ollama service."""
    return OllamaService(ollama)


@router.get("/status", response_model=OllamaStatusResponse)
async def get_ollama_status(service: OllamaService = Depends(get_ollama_service)):
    """Check Ollama installation and running status."""
    try:
        status = service.get_status()
        return OllamaStatusResponse(
            success=True,
            **status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/search", response_model=ModelSearchResponse)
async def search_ollama_library(
    q: str = Query("", description="Search query"),
    category: str = Query(None, description="Category filter"),
    service: OllamaService = Depends(get_ollama_service)
):
    """Search Ollama library for available models."""
    try:
        results = service.search_models(query=q, category=category)
        return ModelSearchResponse(
            success=True,
            models=results,
            count=len(results)
        )
    except Exception as e:
        print(f"Error searching Ollama library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/categories", response_model=CategoryResponse)
async def get_ollama_categories(service: OllamaService = Depends(get_ollama_service)):
    """Get list of model categories."""
    try:
        categories = service.get_categories()
        return CategoryResponse(
            success=True,
            categories=categories
        )
    except Exception as e:
        print(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/models", response_model=ChatModelsResponse)
async def get_chat_models(service: OllamaService = Depends(get_ollama_service)):
    """Get available chat models from Ollama."""
    try:
        models = service.get_chat_models()
        return ChatModelsResponse(
            success=True,
            models=models
        )
    except Exception as e:
        print(f"Error getting chat models: {e}")
        raise HTTPException(status_code=500, detail=str(e))
