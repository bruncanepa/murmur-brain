"""
FastAPI dependency injection providers.

Provides dependency functions for use with FastAPI's Depends() pattern.
"""
from typing import Generator
from .database import DatabaseConnection, get_db_connection
from .ollama_client import OllamaClient, get_ollama_client
from .config import Settings, get_settings


def get_db() -> DatabaseConnection:
    """
    Dependency that provides database connection.

    Usage:
        @app.get("/endpoint")
        def endpoint(db: DatabaseConnection = Depends(get_db)):
            ...
    """
    return get_db_connection()


def get_ollama() -> OllamaClient:
    """
    Dependency that provides Ollama client.

    Usage:
        @app.get("/endpoint")
        def endpoint(ollama: OllamaClient = Depends(get_ollama)):
            ...
    """
    return get_ollama_client()


def get_config() -> Settings:
    """
    Dependency that provides application settings.

    Usage:
        @app.get("/endpoint")
        def endpoint(config: Settings = Depends(get_config)):
            ...
    """
    return get_settings()
