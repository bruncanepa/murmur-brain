const axios = require('axios');

const DEFAULT_API_PORT = 8000;

class ApiService {
  constructor() {
    this.port = DEFAULT_API_PORT;
    this.baseURL = `http://127.0.0.1:${this.port}`;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 300000, // 5 minutes for large file uploads
    });
  }

  setPort(port) {
    this.port = port;
    this.baseURL = `http://127.0.0.1:${port}`;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 300000,
    });
    console.log(`API service configured for port ${port}`);
  }

  async healthCheck() {
    try {
      const response = await this.client.get('/api/health');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async processDocument(filePath) {
    try {
      const FormData = require('form-data');
      const fs = require('fs');

      const formData = new FormData();
      formData.append('file', fs.createReadStream(filePath));

      const response = await this.client.post('/api/documents/process', formData, {
        headers: formData.getHeaders(),
      });

      return { success: true, ...response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      return { success: false, error: errorMessage };
    }
  }

  async getDocuments() {
    try {
      const response = await this.client.get('/api/documents');
      return { success: true, documents: response.data.documents };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getDocument(docId) {
    try {
      const response = await this.client.get(`/api/documents/${docId}`);
      return { success: true, document: response.data.document };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async deleteDocument(docId) {
    try {
      const response = await this.client.delete(`/api/documents/${docId}`);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getStats() {
    try {
      const response = await this.client.get('/api/stats');
      return { success: true, stats: response.data.stats };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async search(query, topK = 5, threshold = 0.0, docIds = null) {
    try {
      const params = new URLSearchParams({
        query: query,
        top_k: topK,
        threshold: threshold
      });

      if (docIds && docIds.length > 0) {
        docIds.forEach(id => params.append('doc_ids', id));
      }

      const response = await this.client.post(`/api/search?${params.toString()}`);
      return { success: true, ...response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      return { success: false, error: errorMessage };
    }
  }
}

module.exports = new ApiService();
