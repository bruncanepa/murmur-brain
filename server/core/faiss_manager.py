"""
FAISS Index Manager for Local Brain.

Provides efficient vector similarity search using Facebook AI Similarity Search (FAISS).
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss
import pickle
import json


class FaissIndexManager:
    """Manages FAISS index for vector similarity search."""

    def __init__(self, index_path: Optional[str] = None, embedding_dim: int = 768):
        """
        Initialize FAISS index manager.

        Args:
            index_path: Path to store/load FAISS index
            embedding_dim: Dimension of embedding vectors
        """
        if index_path is None:
            # Use standard application support directory
            home = Path.home()
            data_dir = home / "Library" / "Application Support" / "murmur-brain"
            data_dir.mkdir(parents=True, exist_ok=True)
            index_path = str(data_dir / "faiss.index")

        self.index_path = index_path
        self.embedding_dim = embedding_dim

        # Initialize FAISS index (IndexFlatIP for cosine similarity)
        self.index = faiss.IndexFlatIP(embedding_dim)

        # Mapping from FAISS index position to vector_id
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}

        # Try to load existing index
        self.load()

    def normalize_embedding(self, embedding: List[float]) -> np.ndarray:
        """
        Normalize embedding for cosine similarity with IndexFlatIP.

        Args:
            embedding: Embedding vector

        Returns:
            Normalized numpy array
        """
        arr = np.array(embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(arr)
        return arr

    def add_vectors(self, vector_ids: List[str], embeddings: List[List[float]]) -> bool:
        """
        Add vectors to the FAISS index.

        Args:
            vector_ids: List of unique vector identifiers
            embeddings: List of embedding vectors

        Returns:
            True if successful
        """
        try:
            if not vector_ids or not embeddings:
                return False

            if len(vector_ids) != len(embeddings):
                raise ValueError("Number of vector_ids must match number of embeddings")

            # Normalize embeddings for cosine similarity
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)

            # Get current index size before adding
            start_index = self.index.ntotal

            # Add to FAISS index
            self.index.add(embeddings_array)

            # Update mappings
            for i, vector_id in enumerate(vector_ids):
                idx = start_index + i
                self.id_to_index[vector_id] = idx
                self.index_to_id[idx] = vector_id

            print(f"Added {len(vector_ids)} vectors to FAISS index (total: {self.index.ntotal})")
            return True

        except Exception as e:
            print(f"Error adding vectors to FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return False

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        vector_ids_filter: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            vector_ids_filter: Optional list of vector IDs to filter by

        Returns:
            List of (vector_id, similarity_score) tuples sorted by similarity
        """
        try:
            if self.index.ntotal == 0:
                print("FAISS index is empty")
                return []

            # Normalize query for cosine similarity
            query_array = self.normalize_embedding(query_embedding)

            # If filtering, need to search more and filter afterwards
            search_k = top_k if not vector_ids_filter else min(self.index.ntotal, top_k * 10)

            # Search FAISS index
            similarities, indices = self.index.search(query_array, search_k)

            # Convert to results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1:  # FAISS returns -1 for empty results
                    continue

                vector_id = self.index_to_id.get(idx)
                if vector_id is None:
                    continue

                # Apply filter if provided
                if vector_ids_filter and vector_id not in vector_ids_filter:
                    continue

                similarity = float(similarities[0][i])
                results.append((vector_id, similarity))

                # Stop if we have enough results
                if len(results) >= top_k:
                    break

            return results

        except Exception as e:
            print(f"Error searching FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return []

    def remove_vectors(self, vector_ids: List[str]) -> bool:
        """
        Remove vectors from the index.

        Note: FAISS IndexFlatIP doesn't support direct removal, so we need to rebuild.
        For small datasets this is acceptable; for large datasets consider using IndexIDMap.

        Args:
            vector_ids: List of vector IDs to remove

        Returns:
            True if successful
        """
        try:
            if not vector_ids:
                return True

            # Mark IDs for removal
            ids_to_remove = set(vector_ids)

            # Check if any IDs exist
            existing_ids = [vid for vid in vector_ids if vid in self.id_to_index]
            if not existing_ids:
                print(f"No vectors found to remove from {len(vector_ids)} requested")
                return True

            print(f"Removing {len(existing_ids)} vectors from FAISS index (rebuilding required)")

            # Rebuild index without removed vectors
            # This is a limitation of IndexFlatIP - for large datasets, consider IndexIDMap
            return self._rebuild_without_ids(ids_to_remove)

        except Exception as e:
            print(f"Error removing vectors from FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _rebuild_without_ids(self, ids_to_remove: set) -> bool:
        """
        Rebuild index without specified IDs.

        Args:
            ids_to_remove: Set of vector IDs to exclude

        Returns:
            True if successful
        """
        try:
            # Collect vectors to keep
            vectors_to_keep = []
            ids_to_keep = []

            for vector_id, idx in self.id_to_index.items():
                if vector_id not in ids_to_remove:
                    # Extract vector from current index
                    vector = self.index.reconstruct(int(idx))
                    vectors_to_keep.append(vector)
                    ids_to_keep.append(vector_id)

            # Create new index
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.id_to_index.clear()
            self.index_to_id.clear()

            # Add kept vectors
            if vectors_to_keep:
                vectors_array = np.array(vectors_to_keep, dtype=np.float32)
                self.index.add(vectors_array)

                for i, vector_id in enumerate(ids_to_keep):
                    self.id_to_index[vector_id] = i
                    self.index_to_id[i] = vector_id

            print(f"Rebuilt FAISS index with {len(ids_to_keep)} vectors")
            return True

        except Exception as e:
            print(f"Error rebuilding FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save(self) -> bool:
        """
        Save FAISS index and mappings to disk.

        Returns:
            True if successful
        """
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)

            # Save mappings
            mappings_path = self.index_path + ".mappings"
            with open(mappings_path, "wb") as f:
                pickle.dump({
                    "id_to_index": self.id_to_index,
                    "index_to_id": self.index_to_id
                }, f)

            print(f"Saved FAISS index to {self.index_path}")
            return True

        except Exception as e:
            print(f"Error saving FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load(self) -> bool:
        """
        Load FAISS index and mappings from disk.

        Returns:
            True if successful, False if files don't exist
        """
        try:
            if not Path(self.index_path).exists():
                print(f"No existing FAISS index found at {self.index_path}")
                return False

            # Load FAISS index
            self.index = faiss.read_index(self.index_path)

            # Load mappings
            mappings_path = self.index_path + ".mappings"
            if Path(mappings_path).exists():
                with open(mappings_path, "rb") as f:
                    mappings = pickle.load(f)
                    self.id_to_index = mappings["id_to_index"]
                    # Convert keys to int for index_to_id
                    self.index_to_id = {int(k): v for k, v in mappings["index_to_id"].items()}

            print(f"Loaded FAISS index from {self.index_path} ({self.index.ntotal} vectors)")
            return True

        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            # Start fresh if loading fails
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.id_to_index.clear()
            self.index_to_id.clear()
            return False

    def build_from_database(self, db_connection) -> bool:
        """
        Build FAISS index from existing vectors in database.

        Args:
            db_connection: DatabaseConnection instance

        Returns:
            True if successful
        """
        try:
            print("Building FAISS index from database vectors...")

            # Fetch all vectors with embeddings
            query = """
                SELECT id, embedding
                FROM vectors
                WHERE embedding IS NOT NULL
                ORDER BY id
            """
            rows = db_connection.fetchall(query)

            if not rows:
                print("No vectors found in database")
                return True

            # Collect vectors
            vector_ids = []
            embeddings = []

            for row in rows:
                vector_id = row["id"]
                embedding_blob = row["embedding"]

                if not embedding_blob:
                    continue

                # Decode embedding
                try:
                    embedding = json.loads(embedding_blob.decode('utf-8'))
                    vector_ids.append(vector_id)
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"Error decoding embedding for vector {vector_id}: {e}")
                    continue

            # Add to index
            if vector_ids and embeddings:
                success = self.add_vectors(vector_ids, embeddings)
                if success:
                    # Save index
                    self.save()
                    print(f"Successfully built FAISS index with {len(vector_ids)} vectors")
                    return True

            return False

        except Exception as e:
            print(f"Error building FAISS index from database: {e}")
            import traceback
            traceback.print_exc()
            return False

    def clear(self) -> bool:
        """
        Clear the index completely.

        Returns:
            True if successful
        """
        try:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.id_to_index.clear()
            self.index_to_id.clear()
            print("Cleared FAISS index")
            return True

        except Exception as e:
            print(f"Error clearing FAISS index: {e}")
            return False
