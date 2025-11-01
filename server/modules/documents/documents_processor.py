"""
File processor for document chunking.

Handles PDF and TXT file processing with intelligent markdown-based chunking.
"""
import os
from pathlib import Path
from typing import Dict, List
import pymupdf4llm
import tiktoken
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter
)
from core.config import get_settings


class FileProcessor:
    """Process documents and create text chunks."""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        settings = get_settings()

        # Use token-based settings if markdown chunking is enabled
        if settings.use_markdown_chunking:
            self.chunk_size = chunk_size or settings.chunk_size_tokens
            self.chunk_overlap = chunk_overlap or settings.chunk_overlap_tokens
            self.use_markdown = True
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            # Fallback to character-based chunking
            self.chunk_size = chunk_size or settings.chunk_size
            self.chunk_overlap = chunk_overlap or settings.chunk_overlap
            self.use_markdown = False
            self.tokenizer = None

        self.max_file_size = settings.max_file_size
        self.preserve_structure = settings.preserve_document_structure

    def validate_file(self, file_path: str) -> Dict:
        """
        Validate file exists, size, and type.

        Args:
            file_path: Path to file

        Returns:
            Dict with validation results
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return {"valid": False, "error": "File does not exist"}

            file_size = path.stat().st_size

            if file_size > self.max_file_size:
                size_mb = file_size / (1024 * 1024)
                max_mb = self.max_file_size / (1024 * 1024)
                return {
                    "valid": False,
                    "error": f"File too large: {size_mb:.2f}MB (max {max_mb:.0f}MB)"
                }

            ext = path.suffix.lower()
            if ext not in ['.pdf', '.txt']:
                return {
                    "valid": False,
                    "error": f"Unsupported file type: {ext}. Only PDF and TXT files are supported."
                }

            return {
                "valid": True,
                "size": file_size,
                "type": ext
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens in

        Returns:
            Number of tokens
        """
        if not self.tokenizer:
            # Fallback to character-based estimation
            return len(text) // 4
        return len(self.tokenizer.encode(text))

    def _detect_structure_type(self, text: str) -> str:
        """
        Detect the structure type of a text chunk.

        Args:
            text: Text to analyze

        Returns:
            Structure type: 'paragraph', 'list', 'table', or 'code'
        """
        text = text.strip()

        # Check for markdown table
        if '|' in text and text.count('|') >= 4:
            return 'table'

        # Check for code block
        if text.startswith('```') or text.count('    ') > 3:
            return 'code'

        # Check for list
        if any(text.startswith(marker) for marker in ['- ', '* ', '+ ', '1. ', '2. ', '3. ']):
            return 'list'

        return 'paragraph'

    def _convert_text_to_markdown(self, text: str) -> str:
        """
        Convert plain text to markdown with structure detection.

        Args:
            text: Plain text

        Returns:
            Markdown-formatted text
        """
        if not text.strip():
            return ""

        lines = text.split('\n')
        markdown_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue

            # Detect potential headers (all caps lines or short lines followed by empty line)
            if len(line) < 60 and line.isupper():
                markdown_lines.append(f"## {line.title()}")
            elif line.endswith(':') and len(line) < 60:
                markdown_lines.append(f"### {line}")
            else:
                markdown_lines.append(line)

        return '\n'.join(markdown_lines)

    def _create_chunks_langchain(self, markdown_text: str) -> List[Dict]:
        """
        Create chunks using LangChain splitters with markdown awareness.

        Args:
            markdown_text: Markdown-formatted text

        Returns:
            List of chunk dictionaries with metadata
        """
        if not markdown_text.strip():
            return []

        chunks = []

        try:
            # Stage 1: Split by markdown headers if structure preservation is enabled
            if self.preserve_structure:
                header_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=[
                        ("# ", "h1"),
                        ("## ", "h2"),
                        ("### ", "h3"),
                    ]
                )
                header_splits = header_splitter.split_text(markdown_text)
            else:
                # Create a simple split object if no header splitting
                from langchain.schema import Document
                header_splits = [Document(page_content=markdown_text, metadata={})]

            # Stage 2: Further split by tokens using RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                encoding_name="cl100k_base",
                # Split on markdown-aware separators
                separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]
            )

            # Process each header section
            chunk_index = 0
            for doc in header_splits:
                # Split the section into token-based chunks
                section_chunks = text_splitter.split_text(doc.page_content)

                for chunk_text in section_chunks:
                    if not chunk_text.strip():
                        continue

                    # Extract headers from metadata
                    headers = []
                    for key in ['h1', 'h2', 'h3']:
                        if key in doc.metadata and doc.metadata[key]:
                            headers.append(f"{'#' * int(key[1])} {doc.metadata[key]}")

                    chunks.append({
                        "text": chunk_text.strip(),
                        "index": chunk_index,
                        "token_count": self._count_tokens(chunk_text),
                        "headers": headers,
                        "structure_type": self._detect_structure_type(chunk_text)
                    })
                    chunk_index += 1

        except Exception as e:
            print(f"Error in LangChain chunking: {e}")
            # Fallback to simple chunking
            print("Falling back to simple text splitting...")
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                encoding_name="cl100k_base"
            )
            simple_chunks = text_splitter.split_text(markdown_text)
            chunks = [
                {
                    "text": chunk.strip(),
                    "index": i,
                    "token_count": self._count_tokens(chunk),
                    "headers": [],
                    "structure_type": self._detect_structure_type(chunk)
                }
                for i, chunk in enumerate(simple_chunks) if chunk.strip()
            ]

        return chunks

    def create_chunks(self, text: str) -> List[Dict]:
        """
        Create overlapping chunks from text with intelligent boundary detection.

        Args:
            text: Input text to chunk

        Returns:
            List of chunk dictionaries
        """
        # Use markdown-based chunking if enabled
        if self.use_markdown:
            markdown_text = self._convert_text_to_markdown(text)
            return self._create_chunks_langchain(markdown_text)

        # Legacy character-based chunking
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
        Process PDF using pymupdf4llm for better extraction quality.
        Extracts PDF as clean Markdown with proper formatting for equations,
        tables, and document structure.

        Args:
            file_path: Path to PDF file

        Returns:
            Dict with chunks and metadata

        Raises:
            Exception: If PDF processing fails
        """
        try:
            print(f"Processing PDF with pymupdf4llm: {Path(file_path).name}")

            # Use pymupdf4llm to extract PDF as clean Markdown
            # This provides much better handling of:
            # - Mathematical equations (LaTeX-style formatting)
            # - Tables and structured data
            # - Multi-column layouts
            # - Document structure (headers, sections)
            markdown_text = pymupdf4llm.to_markdown(file_path)

            print(f"Extracted {len(markdown_text)} characters of markdown text")

            # Count pages from the original PDF for metadata
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()

            # Now process markdown text with appropriate chunking method
            if self.use_markdown:
                # Use LangChain chunking directly on the markdown
                print("Creating intelligent markdown-aware chunks...")
                chunks = self._create_chunks_langchain(markdown_text)
            else:
                # Legacy character-based chunking
                print("Creating character-based chunks...")
                chunks = []
                chunk_index = 0
                start_pos = 0

                while start_pos < len(markdown_text):
                    end_pos = start_pos + self.chunk_size
                    chunk_text = markdown_text[start_pos:end_pos]

                    # Try to end at sentence boundary if not at end
                    if end_pos < len(markdown_text):
                        last_period = chunk_text.rfind('.')
                        last_newline = chunk_text.rfind('\n')
                        boundary_index = max(last_period, last_newline)

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

            print(f"PDF processing complete: {total_pages} pages, "
                  f"{len(markdown_text)} characters, {len(chunks)} chunks")

            # Calculate total tokens if using token-based chunking
            total_tokens = sum(chunk.get("token_count", 0) for chunk in chunks) if self.use_markdown else 0

            metadata = {
                "pageCount": total_pages,
                "characterCount": len(markdown_text),
                "wordCount": len(markdown_text.split()),
                "chunkCount": len(chunks)
            }

            if self.use_markdown:
                metadata["totalTokens"] = total_tokens
                metadata["avgTokensPerChunk"] = total_tokens // len(chunks) if chunks else 0

            return {
                "chunks": chunks,
                "metadata": metadata
            }

        except Exception as e:
            print(f"PDF processing error: {e}")
            raise Exception(f"Failed to process PDF: {str(e)}")

    def process_text(self, file_path: str) -> Dict:
        """
        Process plain text file and create chunks.

        Args:
            file_path: Path to text file

        Returns:
            Dict with chunks and metadata

        Raises:
            Exception: If text processing fails
        """
        try:
            print(f"Processing text file: {Path(file_path).name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Use appropriate chunking method
            if self.use_markdown:
                markdown_text = self._convert_text_to_markdown(text)
                chunks = self._create_chunks_langchain(markdown_text)
            else:
                chunks = self.create_chunks(text)

            # Count lines and words
            lines = text.split('\n')
            words = text.split()

            print(f"Text processing complete: {len(lines)} lines, "
                  f"{len(words)} words, {len(chunks)} chunks")

            # Calculate total tokens if using token-based chunking
            total_tokens = sum(chunk.get("token_count", 0) for chunk in chunks) if self.use_markdown else 0

            metadata = {
                "lineCount": len(lines),
                "wordCount": len(words),
                "characterCount": len(text),
                "chunkCount": len(chunks)
            }

            if self.use_markdown:
                metadata["totalTokens"] = total_tokens
                metadata["avgTokensPerChunk"] = total_tokens // len(chunks) if chunks else 0

            return {
                "chunks": chunks,
                "metadata": metadata
            }

        except Exception as e:
            print(f"Text processing error: {e}")
            raise Exception(f"Failed to process text: {str(e)}")
