"""
Ollama models.

Defines Pydantic schemas for Ollama API.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class OllamaStatusResponse(BaseModel):
    """Schema for Ollama status response."""
    success: bool
    installed: bool
    running: bool
    message: str


class ModelSearchResponse(BaseModel):
    """Schema for model search response."""
    success: bool
    models: List[Dict[str, Any]]
    count: int


class CategoryResponse(BaseModel):
    """Schema for category list response."""
    success: bool
    categories: List[str]


class ChatModelsResponse(BaseModel):
    """Schema for available chat models response."""
    success: bool
    models: List[str]
