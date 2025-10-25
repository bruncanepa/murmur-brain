const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');

class VectorDatabase {
  constructor() {
    this.db = null;
    this.initialized = false;
  }

  /**
   * Initialize the database
   */
  initialize() {
    try {
      // Create database directory in user data folder
      const userDataPath = app.getPath('userData');
      const dbPath = path.join(userDataPath, 'local-brain.db');

      console.log('Initializing database at:', dbPath);

      // Create database connection
      this.db = new Database(dbPath);

      // Enable WAL mode for better concurrency
      this.db.pragma('journal_mode = WAL');

      // Load sqlite-vec extension
      try {
        const sqliteVecPath = require.resolve('sqlite-vec');
        this.db.loadExtension(sqliteVecPath);
        console.log('sqlite-vec extension loaded successfully');
      } catch (error) {
        console.warn('Could not load sqlite-vec extension:', error.message);
        console.log('Vector similarity search will use fallback implementation');
      }

      // Create tables
      this.createTables();

      this.initialized = true;
      console.log('Database initialized successfully');

      return { success: true };
    } catch (error) {
      console.error('Failed to initialize database:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Create database tables
   */
  createTables() {
    // Documents table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        file_path TEXT,
        file_type TEXT NOT NULL,
        file_size INTEGER,
        upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        chunk_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending'
      )
    `);

    // Vectors table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS vectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        embedding BLOB,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
      )
    `);

    // Create indexes for better performance
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_vectors_doc_id ON vectors(doc_id);
      CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);
    `);

    console.log('Database tables created successfully');
  }

  /**
   * Add a document to the database
   */
  addDocument(fileInfo) {
    try {
      const stmt = this.db.prepare(`
        INSERT INTO documents (file_name, file_path, file_type, file_size, chunk_count)
        VALUES (?, ?, ?, ?, ?)
      `);

      const result = stmt.run(
        fileInfo.fileName,
        fileInfo.filePath,
        fileInfo.fileType,
        fileInfo.fileSize || 0,
        fileInfo.chunkCount || 0
      );

      return {
        success: true,
        documentId: result.lastInsertRowid,
      };
    } catch (error) {
      console.error('Error adding document:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Add a vector chunk to the database
   */
  addVector(docId, chunkIndex, chunkText, embedding) {
    try {
      const stmt = this.db.prepare(`
        INSERT INTO vectors (doc_id, chunk_index, chunk_text, embedding)
        VALUES (?, ?, ?, ?)
      `);

      const embeddingBuffer = embedding ? Buffer.from(JSON.stringify(embedding)) : null;

      const result = stmt.run(docId, chunkIndex, chunkText, embeddingBuffer);

      return {
        success: true,
        vectorId: result.lastInsertRowid,
      };
    } catch (error) {
      console.error('Error adding vector:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Add multiple vectors in a transaction
   */
  addVectors(docId, chunks) {
    try {
      const insert = this.db.prepare(`
        INSERT INTO vectors (doc_id, chunk_index, chunk_text, embedding)
        VALUES (?, ?, ?, ?)
      `);

      const insertMany = this.db.transaction((vectors) => {
        for (const vector of vectors) {
          const embeddingBuffer = vector.embedding
            ? Buffer.from(JSON.stringify(vector.embedding))
            : null;
          insert.run(docId, vector.index, vector.text, embeddingBuffer);
        }
      });

      insertMany(chunks);

      return { success: true, count: chunks.length };
    } catch (error) {
      console.error('Error adding vectors:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get all documents
   */
  getDocuments() {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM documents ORDER BY upload_date DESC
      `);

      const documents = stmt.all();

      return {
        success: true,
        documents,
      };
    } catch (error) {
      console.error('Error getting documents:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Get document by ID
   */
  getDocument(docId) {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM documents WHERE id = ?
      `);

      const document = stmt.get(docId);

      return {
        success: true,
        document,
      };
    } catch (error) {
      console.error('Error getting document:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Get vectors for a document
   */
  getVectors(docId) {
    try {
      const stmt = this.db.prepare(`
        SELECT id, chunk_index, chunk_text, embedding
        FROM vectors
        WHERE doc_id = ?
        ORDER BY chunk_index
      `);

      const vectors = stmt.all(docId);

      // Parse embeddings from buffer
      const parsedVectors = vectors.map((v) => ({
        ...v,
        embedding: v.embedding ? JSON.parse(v.embedding.toString()) : null,
      }));

      return {
        success: true,
        vectors: parsedVectors,
      };
    } catch (error) {
      console.error('Error getting vectors:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Search vectors by similarity (basic implementation)
   * This will be enhanced with proper vector similarity in Step 7
   */
  searchVectors(queryEmbedding, limit = 5) {
    try {
      // For now, return recent chunks
      // This will be replaced with proper vector similarity search
      const stmt = this.db.prepare(`
        SELECT v.*, d.file_name
        FROM vectors v
        JOIN documents d ON v.doc_id = d.id
        WHERE v.embedding IS NOT NULL
        ORDER BY v.created_at DESC
        LIMIT ?
      `);

      const results = stmt.all(limit);

      return {
        success: true,
        results,
      };
    } catch (error) {
      console.error('Error searching vectors:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Delete a document and its vectors
   */
  deleteDocument(docId) {
    try {
      const stmt = this.db.prepare('DELETE FROM documents WHERE id = ?');
      stmt.run(docId);

      return { success: true };
    } catch (error) {
      console.error('Error deleting document:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Update document status
   */
  updateDocumentStatus(docId, status) {
    try {
      const stmt = this.db.prepare(`
        UPDATE documents SET status = ? WHERE id = ?
      `);

      stmt.run(status, docId);

      return { success: true };
    } catch (error) {
      console.error('Error updating document status:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Get database statistics
   */
  getStats() {
    try {
      const docCount = this.db.prepare('SELECT COUNT(*) as count FROM documents').get();
      const vectorCount = this.db.prepare('SELECT COUNT(*) as count FROM vectors').get();

      return {
        success: true,
        stats: {
          documentCount: docCount.count,
          vectorCount: vectorCount.count,
        },
      };
    } catch (error) {
      console.error('Error getting stats:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Close database connection
   */
  close() {
    if (this.db) {
      this.db.close();
      this.initialized = false;
      console.log('Database connection closed');
    }
  }
}

// Export singleton instance
module.exports = new VectorDatabase();
