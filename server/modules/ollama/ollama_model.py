"""
Ollama models.

Defines Pydantic schemas for Ollama API.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class InstallationInstructions(BaseModel):
    """Schema for platform-specific installation instructions."""
    platform: str
    method: str
    steps: List[str]
    download_url: str
    command: Optional[str] = None


class PlatformInfo(BaseModel):
    """Schema for platform information."""
    system: str
    machine: str
    platform: str


class OllamaStatusResponse(BaseModel):
    """Schema for enhanced Ollama status response."""
    success: bool
    installed: bool
    running: bool
    ready: bool
    action: str  # One of: "ready", "install_required", "start_service"
    message: str
    installation_instructions: Optional[InstallationInstructions] = None
    platform: Optional[PlatformInfo] = None


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
