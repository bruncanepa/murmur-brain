"""
Document service with business logic.

Handles document processing, embedding generation, and storage coordination.
"""
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import UploadFile
from .documents_model import DocumentRepository, DocumentCreate, DocumentResponse
from .documents_processor import FileProcessor
from core.ollama_client import OllamaClient
from core.database import DatabaseConnection


class DocumentService:
    """Service for document operations with dependency injection."""

    def __init__(
        self,
        doc_repo: DocumentRepository,
        ollama_client: OllamaClient,
        file_processor: FileProcessor
    ):
        self.doc_repo = doc_repo
        self.ollama = ollama_client
        self.processor = file_processor

    async def process_document(
        self,
        file: UploadFile,
        generate_embeddings: bool = True
    ) -> Dict:
        """
        Process an uploaded document with embeddings.

        Args:
            file: Uploaded file
            generate_embeddings: Whether to generate embeddings (default: True)

        Returns:
            Dict with processing results

        Raises:
            Exception: If processing fails
        """
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in ['.pdf', '.txt']:
            raise ValueError(f"Unsupported file type: {file_ext}. Only PDF and TXT files are supported.")

        # Read file contents asynchronously
        file_contents = await file.read()

        # Create temp file and write contents
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_contents)
            temp_file.flush()  # Ensure buffer is written to disk

        try:
            # Validate file
            validation = self.processor.validate_file(temp_path)
            if not validation["valid"]:
                raise ValueError(validation["error"])

            # Process file based on type
            if file_ext == '.pdf':
                result = self.processor.process_pdf_streaming(temp_path)
            elif file_ext == '.txt':
                result = self.processor.process_text(temp_path)
            else:
                raise ValueError("Unsupported file type")

            # Generate embeddings if requested
            if generate_embeddings:
                print(f"Generating embeddings for {len(result['chunks'])} chunks...")
                chunk_texts = [chunk["text"] for chunk in result["chunks"]]
                embeddings = self.ollama.generate_embeddings_batch(chunk_texts, batch_size=5)

                # Attach embeddings to chunks
                for i, chunk in enumerate(result["chunks"]):
                    chunk["embedding"] = embeddings[i] if i < len(embeddings) else []

                print(f"Embeddings generated: {len([e for e in embeddings if e])} successful")

            # Save document to database
            document = DocumentCreate(
                file_name=file.filename,
                file_path=temp_path,
                file_type=file_ext,
                file_size=validation["size"],
                chunk_count=len(result["chunks"])
            )

            doc_id = self.doc_repo.create(document)

            # Save vectors
            vector_count = self.doc_repo.add_vectors(doc_id, result["chunks"])

            # Update status
            self.doc_repo.update_status(doc_id, "completed")

            return {
                "success": True,
                "documentId": doc_id,
                "metadata": {
                    "fileName": file.filename,
                    "fileType": file_ext,
                    "fileSize": validation["size"],
                    **result["metadata"]
                },
                "chunkCount": vector_count
            }

        except Exception as e:
            # Cleanup on error
            Path(temp_path).unlink(missing_ok=True)
            raise e

    async def process_document_stream_bytes(
        self,
        file_contents: bytes,
        filename: str,
        progress_callback=None
    ):
        """
        Process document from bytes with streaming progress updates.

        Args:
            file_contents: File contents as bytes
            filename: Original filename
            progress_callback: Async callback for progress updates

        Yields:
            Progress update dictionaries
        """
        file_ext = Path(filename).suffix.lower()

        temp_path = None

        try:
            # Upload phase (5%)
            if progress_callback:
                await progress_callback("upload", 5, f"Uploading {filename}...")

            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as temp_file:
                temp_path = temp_file.name
                temp_file.write(file_contents)
                temp_file.flush()  # Ensure buffer is written to disk

            # Validation phase (10%)
            if progress_callback:
                await progress_callback("validation", 10, "Validating file...")

            validation = self.processor.validate_file(temp_path)
            if not validation["valid"]:
                raise ValueError(validation["error"])

            # Extraction phase (30%)
            if progress_callback:
                await progress_callback("extraction", 15, f"Extracting text from {file_ext.upper()}...")

            if file_ext == '.pdf':
                result = self.processor.process_pdf_streaming(temp_path)
            elif file_ext == '.txt':
                result = self.processor.process_text(temp_path)
            else:
                raise ValueError("Unsupported file type")

            chunk_count = len(result['chunks'])
            if progress_callback:
                await progress_callback("extraction", 30, f"Extracted {chunk_count} chunks",
                                      {"chunks": chunk_count})

            # Embedding phase (30-85%)
            if progress_callback:
                await progress_callback("embedding", 30, f"Generating embeddings for {chunk_count} chunks...")

            chunk_texts = [chunk["text"] for chunk in result["chunks"]]
            embeddings = []
            batch_size = 5

            for i in range(0, chunk_count, batch_size):
                batch = chunk_texts[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (chunk_count + batch_size - 1) // batch_size

                progress = 30 + int((i / chunk_count) * 55)
                if progress_callback:
                    await progress_callback("embedding", progress,
                                          f"Processing batch {batch_num}/{total_batches}",
                                          {"batch": batch_num, "totalBatches": total_batches})

                for text in batch:
                    try:
                        embedding = self.ollama.generate_embedding(text)
                        embeddings.append(embedding)
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"Error generating embedding: {e}")
                        embeddings.append([])

            # Attach embeddings
            for i, chunk in enumerate(result["chunks"]):
                chunk["embedding"] = embeddings[i] if i < len(embeddings) else []

            if progress_callback:
                await progress_callback("embedding", 85, f"Generated {len([e for e in embeddings if e])} embeddings")

            # Storage phase (85-95%)
            if progress_callback:
                await progress_callback("storage", 85, "Saving document to database...")

            document = DocumentCreate(
                file_name=filename,
                file_path=temp_path,
                file_type=file_ext,
                file_size=validation["size"],
                chunk_count=chunk_count
            )

            doc_id = self.doc_repo.create(document)

            if progress_callback:
                await progress_callback("storage", 90, "Saving chunks and vectors...")

            self.doc_repo.add_vectors(doc_id, result["chunks"])
            self.doc_repo.update_status(doc_id, "completed")

            # Complete (100%)
            if progress_callback:
                await progress_callback("complete", 100, "Document processed successfully!", {
                    "documentId": doc_id,
                    "fileName": filename,
                    "fileType": file_ext,
                    "fileSize": validation["size"],
                    "chunkCount": chunk_count,
                    **result["metadata"]
                })

            return doc_id

        except Exception as e:
            if progress_callback:
                await progress_callback("error", 0, str(e))
            raise e

        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        """Get document by ID."""
        doc = self.doc_repo.get_by_id(doc_id)
        if doc:
            return DocumentResponse(**doc)
        return None

    def get_all_documents(self) -> List[DocumentResponse]:
        """Get all documents."""
        docs = self.doc_repo.get_all()
        return [DocumentResponse(**doc) for doc in docs]

    def delete_document(self, doc_id: str) -> bool:
        """Delete document and its vectors."""
        return self.doc_repo.delete(doc_id)

    def get_stats(self) -> Dict[str, int]:
        """Get document statistics."""
        return self.doc_repo.get_stats()
