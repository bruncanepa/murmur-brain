import os
from pathlib import Path
from typing import Dict, List
import csv
from io import StringIO
from pypdf import PdfReader


class FileProcessor:
    """Process documents and create text chunks"""

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_file_size = 50 * 1024 * 1024  # 50MB

    def validate_file(self, file_path: str) -> Dict:
        """Validate file exists, size, and type"""
        try:
            path = Path(file_path)

            if not path.exists():
                return {"valid": False, "error": "File does not exist"}

            file_size = path.stat().st_size

            if file_size > self.max_file_size:
                size_mb = file_size / (1024 * 1024)
                return {
                    "valid": False,
                    "error": f"File too large: {size_mb:.2f}MB (max 50MB)"
                }

            ext = path.suffix.lower()
            if ext not in ['.pdf', '.csv', '.txt']:
                return {
                    "valid": False,
                    "error": f"Unsupported file type: {ext}"
                }

            return {
                "valid": True,
                "size": file_size,
                "type": ext
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def create_chunks(self, text: str) -> List[Dict]:
        """Create overlapping chunks from text"""
        chunks = []
        chunk_index = 0
        start_pos = 0

        while start_pos < len(text):
            end_pos = start_pos + self.chunk_size

            # Get chunk text
            chunk_text = text[start_pos:end_pos]

            # Try to end at sentence boundary if not at end
            if end_pos < len(text):
                # Look for sentence endings
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                boundary_index = max(last_period, last_newline)

                # If we found a good boundary in the second half of chunk
                if boundary_index > self.chunk_size * 0.5:
                    chunk_text = chunk_text[:boundary_index + 1]
                    end_pos = start_pos + boundary_index + 1

            chunks.append({
                "text": chunk_text.strip(),
                "index": chunk_index,
                "startChar": start_pos,
                "endChar": end_pos
            })

            chunk_index += 1
            start_pos = end_pos - self.chunk_overlap

        return chunks

    def process_pdf_streaming(self, file_path: str) -> Dict:
        """
        Process PDF in streaming mode to avoid memory issues
        Creates chunks incrementally as pages are processed
        """
        try:
            print(f"Processing PDF in streaming mode: {Path(file_path).name}")

            reader = PdfReader(file_path, strict=False)  # Use non-strict mode to handle malformed PDFs
            total_pages = len(reader.pages)

            print(f"PDF has {total_pages} pages. Processing incrementally...")

            chunks = []
            accumulated_text = ""
            chunk_index = 0
            total_chars = 0

            # Process pages one by one
            for page_num in range(total_pages):
                try:
                    page = reader.pages[page_num]
                    page_text = page.extract_text() or ""  # Handle None return
                    total_chars += len(page_text)

                    accumulated_text += page_text + " "
                except Exception as page_error:
                    print(f"Warning: Failed to extract page {page_num + 1}: {page_error}")
                    # Continue with next page
                    continue

                # When we have enough text, create chunks
                while len(accumulated_text) >= self.chunk_size:
                    chunk = accumulated_text[:self.chunk_size]

                    # Try to end at sentence boundary
                    last_period = chunk.rfind('.')
                    last_newline = chunk.rfind('\n')
                    boundary_index = max(last_period, last_newline)

                    final_chunk = chunk
                    consumed_length = self.chunk_size

                    if boundary_index > self.chunk_size * 0.5:
                        final_chunk = chunk[:boundary_index + 1]
                        consumed_length = boundary_index + 1

                    chunks.append({
                        "text": final_chunk.strip(),
                        "index": chunk_index,
                        "startChar": total_chars - len(accumulated_text),
                        "endChar": total_chars - len(accumulated_text) + consumed_length
                    })

                    chunk_index += 1

                    # Keep overlap for next chunk
                    accumulated_text = accumulated_text[consumed_length - self.chunk_overlap:]

                # Log progress
                if (page_num + 1) % 10 == 0 or page_num + 1 == total_pages:
                    print(f"Processed {page_num + 1}/{total_pages} pages, created {len(chunks)} chunks so far")

            # Process remaining accumulated text
            if accumulated_text.strip():
                chunks.append({
                    "text": accumulated_text.strip(),
                    "index": chunk_index,
                    "startChar": total_chars - len(accumulated_text),
                    "endChar": total_chars
                })

            print(f"PDF streaming complete: {total_pages} pages, {total_chars} characters, {len(chunks)} chunks")

            return {
                "chunks": chunks,
                "metadata": {
                    "pageCount": total_pages,
                    "characterCount": total_chars,
                    "chunkCount": len(chunks)
                }
            }

        except Exception as e:
            print(f"PDF streaming error: {e}")
            raise Exception(f"Failed to stream PDF: {str(e)}")

    def process_csv(self, file_path: str) -> Dict:
        """Process CSV file and create chunks"""
        try:
            print(f"Processing CSV: {Path(file_path).name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()

            # Parse CSV
            csv_reader = csv.DictReader(StringIO(csv_content))
            rows = list(csv_reader)

            # Convert to text format
            text_parts = []
            for row in rows:
                row_text = ", ".join([f"{k}: {v}" for k, v in row.items()])
                text_parts.append(row_text)

            full_text = "\n".join(text_parts)
            chunks = self.create_chunks(full_text)

            print(f"CSV processing complete: {len(rows)} rows, {len(full_text)} characters, {len(chunks)} chunks")

            return {
                "chunks": chunks,
                "metadata": {
                    "rowCount": len(rows),
                    "columnCount": len(rows[0].keys()) if rows else 0,
                    "characterCount": len(full_text),
                    "chunkCount": len(chunks)
                }
            }

        except Exception as e:
            print(f"CSV processing error: {e}")
            raise Exception(f"Failed to process CSV: {str(e)}")

    def process_text(self, file_path: str) -> Dict:
        """Process plain text file and create chunks"""
        try:
            print(f"Processing text file: {Path(file_path).name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            chunks = self.create_chunks(text)

            # Count lines and words
            lines = text.split('\n')
            words = text.split()

            print(f"Text processing complete: {len(lines)} lines, {len(words)} words, {len(chunks)} chunks")

            return {
                "chunks": chunks,
                "metadata": {
                    "lineCount": len(lines),
                    "wordCount": len(words),
                    "characterCount": len(text),
                    "chunkCount": len(chunks)
                }
            }

        except Exception as e:
            print(f"Text processing error: {e}")
            raise Exception(f"Failed to process text: {str(e)}")
