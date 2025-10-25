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

  // ============ Chat API Methods ============

  async createChat(title = null, docIds = []) {
    try {
      const response = await this.client.post('/api/chats', { title, doc_ids: docIds });
      return { success: true, chatId: response.data.chatId };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      return { success: false, error: errorMessage };
    }
  }

  async getChats() {
    try {
      const response = await this.client.get('/api/chats');
      return { success: true, chats: response.data.chats };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getChat(chatId) {
    try {
      const response = await this.client.get(`/api/chats/${chatId}`);
      return { success: true, chat: response.data.chat, messages: response.data.messages };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async deleteChat(chatId) {
    try {
      await this.client.delete(`/api/chats/${chatId}`);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async sendMessage(chatId, message, model = 'llama3.2') {
    try {
      const response = await this.client.post(`/api/chats/${chatId}/messages`, {
        message,
        model
      });
      return { success: true, ...response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      return { success: false, error: errorMessage };
    }
  }

  async linkDocument(chatId, docId) {
    try {
      await this.client.post(`/api/chats/${chatId}/documents`, { doc_id: docId });
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      return { success: false, error: errorMessage };
    }
  }

  async unlinkDocument(chatId, docId) {
    try {
      await this.client.delete(`/api/chats/${chatId}/documents/${docId}`);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getChatDocuments(chatId) {
    try {
      const response = await this.client.get(`/api/chats/${chatId}/documents`);
      return { success: true, documents: response.data.documents };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async getChatModels() {
    try {
      const response = await this.client.get('/api/chat/models');
      return { success: true, models: response.data.models };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async updateChatTitle(chatId, title) {
    try {
      await this.client.patch(`/api/chats/${chatId}/title`, { title });
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      return { success: false, error: errorMessage };
    }
  }
}

module.exports = new ApiService();
