"""
Configuration management for Murmur Brain backend.

Provides application settings and environment configuration.
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import os


class Settings(BaseModel):
    """Application settings with defaults."""

    # Application
    app_name: str = "Murmur Brain"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    db_path: Optional[str] = None

    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_default_chat_model: str = "llama3.2"
    ollama_timeout: int = 120

    # File Processing
    max_file_size: int = 50 * 1024 * 1024  # 50MB

    # Token-based chunking settings
    chunk_size_tokens: int = 1000
    chunk_overlap_tokens: int = 200
    use_markdown_chunking: bool = True
    preserve_document_structure: bool = True

    # Legacy character-based settings (deprecated, kept for backward compatibility)
    chunk_size: int = 1500
    chunk_overlap: int = 300

    # Vector Search
    default_top_k: int = 5
    default_similarity_threshold: float = 0.0
    embedding_dimensions: int = 768

    # Chat
    rag_context_limit: int = 5
    chat_title_generation: bool = True

    class Config:
        env_prefix = "LOCAL_BRAIN_"
        case_sensitive = False


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
