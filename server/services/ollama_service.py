import requests
from typing import List, Dict
import time


class OllamaService:
    """Service for interacting with Ollama API for embeddings"""

    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url
        self.embedding_model = "nomic-embed-text"

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector (768 dimensions)
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise Exception(f"Failed to generate embedding: {str(e)}")

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of text strings to generate embeddings for
            batch_size: Number of texts to process in each batch

        Returns:
            List of embedding vectors
        """
        embeddings = []
        total = len(texts)

        print(f"Generating embeddings for {total} chunks in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_end = min(i + batch_size, total)

            print(f"Processing batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size} (chunks {i + 1}-{batch_end})")

            for text in batch:
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                    # Small delay to avoid overwhelming Ollama
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error generating embedding for chunk: {e}")
                    # Return empty list on error to maintain index alignment
                    embeddings.append([])

        print(f"Generated {len([e for e in embeddings if e])} embeddings successfully")
        return embeddings

    def check_model_available(self) -> bool:
        """
        Check if the embedding model is available in Ollama

        Returns:
            True if model is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])

            for model in models:
                if model.get("name", "").startswith(self.embedding_model):
                    return True

            return False
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False

    def pull_model(self) -> Dict:
        """
        Pull the embedding model if not available

        Returns:
            Dict with success status and message
        """
        try:
            print(f"Pulling {self.embedding_model} model...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.embedding_model},
                timeout=300  # 5 minutes for download
            )
            response.raise_for_status()
            return {"success": True, "message": f"Model {self.embedding_model} pulled successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_ollama_instance = None

def get_ollama_service() -> OllamaService:
    global _ollama_instance
    if _ollama_instance is None:
        _ollama_instance = OllamaService()
    return _ollama_instance
