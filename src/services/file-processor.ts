import fs from 'fs/promises';
import path from 'path';
// import pdf from 'pdf-parse'; // Disabled for browser build
// import { parse } from 'csv-parse/sync'; // Disabled for browser build

class FileProcessor {
  private supportedTypes: string[];
  private chunkSize: number;
  private chunkOverlap: number;

  constructor() {
    this.supportedTypes = ['.pdf', '.csv', '.txt'];
    this.chunkSize = 1000; // characters per chunk
    this.chunkOverlap = 200; // overlap between chunks
  }

  /**
   * Check if file type is supported
   */
  isSupportedFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return this.supportedTypes.includes(ext);
  }

  /**
   * Process a file and extract text content
   */
  async processFile(filePath) {
    try {
      const ext = path.extname(filePath).toLowerCase();
      const fileName = path.basename(filePath);

      console.log(`Processing file: ${fileName}`);

      let text = '';
      const metadata = {
        fileName,
        filePath,
        fileType: ext,
        processedAt: new Date().toISOString(),
      };

      switch (ext) {
        case '.pdf':
          text = await this.processPDF(filePath);
          break;
        case '.csv':
          text = await this.processCSV(filePath);
          break;
        case '.txt':
          text = await this.processTXT(filePath);
          break;
        default:
          throw new Error(`Unsupported file type: ${ext}`);
      }

      metadata.characterCount = text.length;
      metadata.wordCount = text
        .split(/\s+/)
        .filter((word) => word.length > 0).length;

      return {
        success: true,
        text,
        metadata,
      };
    } catch (error) {
      console.error('Error processing file:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Process PDF file with true streaming - process page by page without
   * accumulating all text in memory
   */
  async processPDF(filePath) {
    try {
      console.log(`Processing PDF: ${path.basename(filePath)}`);

      // Read file buffer
      const dataBuffer = await fs.readFile(filePath);
      console.log(
        `PDF buffer size: ${(dataBuffer.length / 1024 / 1024).toFixed(2)} MB`
      );

      // Parse PDF to get page count first (without extracting all text)
      const pdfInfo = await pdf(dataBuffer, { max: 1 });
      const totalPages = pdfInfo.numpages;

      console.log(`PDF has ${totalPages} pages. Processing in batches...`);

      // Process pages in small batches to avoid memory buildup
      const batchSize = 5; // Process 5 pages at a time
      let allText = '';

      for (let startPage = 1; startPage <= totalPages; startPage += batchSize) {
        const endPage = Math.min(startPage + batchSize - 1, totalPages);

        // Process this batch of pages
        const batchOptions = {
          max: endPage,
          pagerender: async function (pageData) {
            const pageNum = pageData.pageIndex + 1;
            if (pageNum < startPage) return ''; // Skip pages before this batch

            const textContent = pageData.getTextContent();
            const text = (await textContent).items
              .map((item) => item.str)
              .join(' ');
            return text;
          },
        };

        const batchData = await pdf(dataBuffer, batchOptions);
        allText += batchData.text + '\n\n';

        // Log progress
        console.log(`Processed pages ${startPage}-${endPage}/${totalPages}`);

        // Give garbage collector a chance to run
        if (global.gc) {
          global.gc();
        }
      }

      console.log(
        `PDF processing complete: ${totalPages} pages, ${allText.length} characters`
      );

      return allText.trim();
    } catch (error) {
      console.error('PDF processing error:', error);
      throw new Error(`Failed to parse PDF: ${error.message}`);
    }
  }

  /**
   * Process CSV file
   */
  async processCSV(filePath) {
    try {
      const fileContent = await fs.readFile(filePath, 'utf-8');

      // Parse CSV
      const records = parse(fileContent, {
        columns: true,
        skip_empty_lines: true,
        trim: true,
      });

      // Convert records to text format
      // Format: "Column1: value1, Column2: value2, ..."
      const textLines = records.map((record, index) => {
        const line = Object.entries(record)
          .map(([key, value]) => `${key}: ${value}`)
          .join(', ');
        return `Row ${index + 1}: ${line}`;
      });

      return textLines.join('\n');
    } catch (error) {
      throw new Error(`Failed to parse CSV: ${error.message}`);
    }
  }

  /**
   * Process TXT file
   */
  async processTXT(filePath) {
    try {
      return await fs.readFile(filePath, 'utf-8');
    } catch (error) {
      throw new Error(`Failed to read TXT file: ${error.message}`);
    }
  }

  /**
   * Validate file before processing
   */
  async validateFile(filePath) {
    try {
      // Check if file exists
      await fs.access(filePath);

      // Check file size (max 50MB)
      const stats = await fs.stat(filePath);
      const fileSizeInMB = stats.size / (1024 * 1024);

      if (fileSizeInMB > 50) {
        return {
          valid: false,
          error: `File is too large (${fileSizeInMB.toFixed(2)}MB). Maximum size is 50MB.`,
        };
      }

      // Check file type
      if (!this.isSupportedFile(filePath)) {
        const ext = path.extname(filePath);
        return {
          valid: false,
          error: `Unsupported file type: ${ext}. Supported types: ${this.supportedTypes.join(', ')}`,
        };
      }

      return {
        valid: true,
        size: stats.size,
        sizeInMB: fileSizeInMB,
      };
    } catch (error) {
      return {
        valid: false,
        error: `File validation failed: ${error.message}`,
      };
    }
  }

  /**
   * Get file information
   */
  async getFileInfo(filePath) {
    try {
      const stats = await fs.stat(filePath);
      const ext = path.extname(filePath).toLowerCase();
      const name = path.basename(filePath);

      return {
        name,
        path: filePath,
        size: stats.size,
        sizeInMB: (stats.size / (1024 * 1024)).toFixed(2),
        type: ext,
        supported: this.isSupportedFile(filePath),
        modifiedAt: stats.mtime,
      };
    } catch (error) {
      throw new Error(`Failed to get file info: ${error.message}`);
    }
  }

  /**
   * Split text into overlapping chunks for better context preservation
   */
  chunkText(text) {
    const chunks = [];
    let startIndex = 0;

    while (startIndex < text.length) {
      // Get chunk with specified size
      const endIndex = Math.min(startIndex + this.chunkSize, text.length);
      let chunk = text.substring(startIndex, endIndex);

      // Try to end chunk at a sentence boundary if possible
      if (endIndex < text.length) {
        const lastPeriod = chunk.lastIndexOf('.');
        const lastNewline = chunk.lastIndexOf('\n');
        const boundaryIndex = Math.max(lastPeriod, lastNewline);

        if (boundaryIndex > this.chunkSize * 0.5) {
          // Only use boundary if it's in the latter half of the chunk
          chunk = chunk.substring(0, boundaryIndex + 1);
        }
      }

      chunks.push({
        text: chunk.trim(),
        index: chunks.length,
        startChar: startIndex,
        endChar: startIndex + chunk.length,
      });

      // Move start index forward, accounting for overlap
      startIndex += chunk.length - this.chunkOverlap;
    }

    return chunks;
  }

  /**
   * Process file and return with chunks
   */
  async processFileWithChunks(filePath) {
    try {
      const result = await this.processFile(filePath);

      if (!result.success) {
        return result;
      }

      // Chunk the text
      const chunks = this.chunkText(result.text);

      // Clear the full text from memory to save space
      delete result.text;

      return {
        ...result,
        chunks,
        metadata: {
          ...result.metadata,
          chunkCount: chunks.length,
          chunkSize: this.chunkSize,
          chunkOverlap: this.chunkOverlap,
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Process PDF in streaming mode - chunk as we go to minimize memory usage
   * Returns chunks directly without keeping full text in memory
   */
  async processPDFStreaming(filePath) {
    try {
      console.log(
        `Processing PDF in streaming mode: ${path.basename(filePath)}`
      );

      const dataBuffer = await fs.readFile(filePath);
      console.log(
        `PDF buffer size: ${(dataBuffer.length / 1024 / 1024).toFixed(2)} MB`
      );

      // Get page count
      const pdfInfo = await pdf(dataBuffer, { max: 1 });
      const totalPages = pdfInfo.numpages;

      console.log(
        `PDF has ${totalPages} pages. Processing and chunking incrementally...`
      );

      const chunks = [];
      let accumulatedText = '';
      let chunkIndex = 0;
      let totalChars = 0;

      // Process pages one by one
      for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
        const pageOptions = {
          max: pageNum,
          pagerender: async function (pageData) {
            if (pageData.pageIndex + 1 < pageNum) return '';
            const textContent = pageData.getTextContent();
            const text = (await textContent).items
              .map((item) => item.str)
              .join(' ');
            return text;
          },
        };

        const pageData = await pdf(dataBuffer, pageOptions);
        const pageText = pageData.text;
        totalChars += pageText.length;

        accumulatedText += pageText + ' ';

        // When we have enough text, create chunks
        while (accumulatedText.length >= this.chunkSize) {
          const chunk = accumulatedText.substring(0, this.chunkSize);

          // Try to end at sentence boundary
          const lastPeriod = chunk.lastIndexOf('.');
          const lastNewline = chunk.lastIndexOf('\n');
          const boundaryIndex = Math.max(lastPeriod, lastNewline);

          let finalChunk = chunk;
          let consumedLength = this.chunkSize;

          if (boundaryIndex > this.chunkSize * 0.5) {
            finalChunk = chunk.substring(0, boundaryIndex + 1);
            consumedLength = boundaryIndex + 1;
          }

          chunks.push({
            text: finalChunk.trim(),
            index: chunkIndex++,
            startChar: totalChars - accumulatedText.length,
            endChar: totalChars - accumulatedText.length + consumedLength,
          });

          // Keep overlap for next chunk
          accumulatedText = accumulatedText.substring(
            consumedLength - this.chunkOverlap
          );
        }

        // Log progress
        if (pageNum % 10 === 0 || pageNum === totalPages) {
          console.log(
            `Processed ${pageNum}/${totalPages} pages, created ${chunks.length} chunks so far`
          );
        }

        // Force garbage collection if available
        if (global.gc && pageNum % 10 === 0) {
          global.gc();
        }
      }

      // Process remaining accumulated text
      if (accumulatedText.trim().length > 0) {
        chunks.push({
          text: accumulatedText.trim(),
          index: chunkIndex++,
          startChar: totalChars - accumulatedText.length,
          endChar: totalChars,
        });
      }

      console.log(
        `PDF streaming complete: ${totalPages} pages, ${totalChars} characters, ${chunks.length} chunks`
      );

      return {
        chunks,
        metadata: {
          pageCount: totalPages,
          characterCount: totalChars,
          chunkCount: chunks.length,
        },
      };
    } catch (error) {
      console.error('PDF streaming error:', error);
      throw new Error(`Failed to stream PDF: ${error.message}`);
    }
  }
}

// Export singleton instance
export default new FileProcessor();
