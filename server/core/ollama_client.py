"""
Ollama HTTP client for embeddings and chat completions.

Provides a clean interface to interact with the Ollama API.
"""
import requests
import time
from typing import List, Dict, Optional
from .config import get_settings


class OllamaClient:
    """HTTP client for Ollama API interactions."""

    def __init__(self, base_url: Optional[str] = None, embedding_model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.ollama_base_url
        self.embedding_model = embedding_model or settings.ollama_embedding_model
        self.timeout = settings.ollama_timeout

    def generate_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """
        Generate embedding for a single text string with retry logic.

        Args:
            text: Text to generate embedding for
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            List of floats representing the embedding vector (768 dimensions)

        Raises:
            Exception: If embedding generation fails after all retries
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    },
                    timeout=30
                )

                # Log response details if error occurs
                if response.status_code != 200:
                    print(f"❌ Ollama returned {response.status_code} (attempt {attempt + 1}/{max_retries})")
                    print(f"Response body: {response.text}")
                    print(f"Text length: {len(text)} chars")
                    print(f"Text preview: {text[:200]}..." if len(text) > 200 else f"Text: {repr(text)}")

                response.raise_for_status()
                result = response.json()

                # Success - return embedding
                if attempt > 0:
                    print(f"✅ Embedding succeeded on retry {attempt + 1}")
                return result.get("embedding", [])

            except Exception as e:
                last_error = e

                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    print(f"⚠️ Embedding failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    print(f"❌ Embedding failed after {max_retries} attempts: {e}")

        # All retries exhausted
        raise Exception(f"Failed to generate embedding after {max_retries} attempts: {str(last_error)}")

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 5,
        delay: float = 0.5
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches with retry logic.

        Args:
            texts: List of text strings to generate embeddings for
            batch_size: Number of texts to process in each batch (default: 5)
            delay: Delay in seconds between embeddings to allow GPU recovery (default: 0.5s)

        Returns:
            List of embedding vectors
        """
        embeddings = []
        total = len(texts)

        print(f"Generating embeddings for {total} chunks in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_end = min(i + batch_size, total)

            print(f"Processing batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size} "
                  f"(chunks {i + 1}-{batch_end})")

            for text in batch:
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                    # Delay to allow Ollama GPU memory recovery between requests
                    time.sleep(delay)
                except Exception as e:
                    print(f"Error generating embedding for chunk: {e}")
                    # Return empty list on error to maintain index alignment
                    embeddings.append([])

        print(f"Generated {len([e for e in embeddings if e])} embeddings successfully")
        return embeddings

    def check_model_available(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a model is available in Ollama.

        Args:
            model_name: Model name to check (defaults to embedding model)

        Returns:
            True if model is available, False otherwise
        """
        model = model_name or self.embedding_model
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])

            for m in models:
                if m.get("name", "").startswith(model):
                    return True

            return False
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False

    def pull_model(self, model_name: Optional[str] = None) -> Dict:
        """
        Pull a model if not available.

        Args:
            model_name: Model name to pull (defaults to embedding model)

        Returns:
            Dict with success status and message
        """
        model = model_name or self.embedding_model
        try:
            print(f"Pulling {model} model...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=300  # 5 minutes for download
            )
            response.raise_for_status()
            return {"success": True, "message": f"Model {model} pulled successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_chat_response(
        self,
        messages: List[Dict],
        model: str,
        stream: bool = False
    ) -> str:
        """
        Generate chat response using Ollama.

        Args:
            messages: List of message dicts with role and content
            model: Ollama model to use for chat
            stream: Whether to stream the response

        Returns:
            Generated response string

        Raises:
            Exception: If chat generation fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            print(f"Error generating chat response: {e}")
            raise Exception(f"Failed to generate chat response: {str(e)}")

    def list_models(self) -> List[Dict]:
        """
        List all available models in Ollama.

        Returns:
            List of model dictionaries
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def list_chat_models(self) -> List[str]:
        """
        List available chat models (excluding embedding-only models).

        Returns:
            List of model names
        """
        try:
            models = self.list_models()

            # Filter out embedding models
            chat_models = []
            for model in models:
                model_name = model.get("name", "")
                # Exclude embedding-only models
                if not any(embed in model_name.lower() for embed in ["embed", "embedding"]):
                    chat_models.append(model_name)

            return chat_models
        except Exception as e:
            print(f"Error listing chat models: {e}")
            return []


# Singleton Ollama client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create the singleton Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
