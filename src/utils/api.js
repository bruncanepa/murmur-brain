import axios from 'axios';

// Auto-detect API URL based on environment
const getApiUrl = () => {
  // In development, use localhost
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }
  // In production (PWA served by Python), API is at same origin
  return window.location.origin;
};

const API_URL = getApiUrl();

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Service
export const apiService = {
  // Health Check
  async healthCheck() {
    const response = await api.get('/api/health');
    return response.data;
  },

  // Document Operations
  async uploadDocument(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    // Use SSE endpoint for real-time progress
    const url = `${API_URL}/api/documents/process-stream`;

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      let lastEventData = null;

      xhr.open('POST', url, true);

      // Track upload progress (file transfer to server)
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const uploadPercent = Math.min(Math.round((e.loaded / e.total) * 5), 5);
          onProgress({
            phase: 'upload',
            progress: uploadPercent,
            message: 'Uploading file...'
          });
        }
      });

      // Handle SSE stream for processing progress
      xhr.addEventListener('readystatechange', () => {
        if (xhr.readyState === 3 || xhr.readyState === 4) {
          // Parse SSE events from response text
          const lines = xhr.responseText.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const eventData = JSON.parse(line.substring(6));
                lastEventData = eventData;

                if (onProgress) {
                  onProgress(eventData);
                }
              } catch (e) {
                console.error('Failed to parse SSE event:', e);
              }
            }
          }
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          // Return the last event data (should be the complete event)
          if (lastEventData && lastEventData.phase === 'complete') {
            resolve({
              success: true,
              documentId: lastEventData.details.documentId,
              metadata: {
                fileName: lastEventData.details.fileName,
                fileType: lastEventData.details.fileType,
                fileSize: lastEventData.details.fileSize,
                characterCount: lastEventData.details.characterCount,
                wordCount: lastEventData.details.wordCount
              },
              chunkCount: lastEventData.details.chunkCount
            });
          } else if (lastEventData && lastEventData.phase === 'error') {
            reject(new Error(lastEventData.message));
          } else {
            reject(new Error('Upload completed but no completion event received'));
          }
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload was aborted'));
      });

      xhr.send(formData);
    });
  },

  async getDocuments() {
    const response = await api.get('/api/documents');
    return response.data;
  },

  async getDocument(id) {
    const response = await api.get(`/api/documents/${id}`);
    return response.data;
  },

  async deleteDocument(id) {
    const response = await api.delete(`/api/documents/${id}`);
    return response.data;
  },

  async getStats() {
    const response = await api.get('/api/stats');
    return response.data;
  },

  // Search Operations
  async search(query, topK = 5, threshold = 0.0, docIds = null) {
    const params = {
      query,
      top_k: topK,
      threshold,
    };

    // Add doc_ids only if provided (as comma-separated string)
    if (docIds && Array.isArray(docIds) && docIds.length > 0) {
      params.doc_ids = docIds.join(',');
    }

    const response = await api.get('/api/search', { params });
    return response.data;
  },

  // Ollama Operations (direct to Ollama API)
  async getOllamaStatus() {
    try {
      const response = await axios.get('http://127.0.0.1:11434/api/tags', {
        timeout: 5000,
      });
      return {
        running: true,
        models: response.data.models || [],
      };
    } catch (error) {
      return {
        running: false,
        models: [],
        error: error.message,
      };
    }
  },

  async pullModel(modelName, onProgress, abortSignal = null) {
    try {
      const response = await fetch('http://127.0.0.1:11434/api/pull', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: modelName }),
        signal: abortSignal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter((line) => line.trim());

        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (onProgress) {
              onProgress(data);
            }
          } catch (e) {
            console.error('Failed to parse progress:', e);
          }
        }
      }

      return { success: true };
    } catch (error) {
      if (error.name === 'AbortError') {
        return { success: false, error: 'Download cancelled', cancelled: true };
      }
      return { success: false, error: error.message };
    }
  },

  async deleteModel(modelName) {
    try {
      const response = await axios.delete('http://127.0.0.1:11434/api/delete', {
        data: { name: modelName },
      });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  async searchOllamaLibrary(query = '', category = null) {
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (category) params.append('category', category);

      const response = await api.get(`/api/ollama/library/search?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error searching Ollama library:', error);
      return { success: false, error: error.message, models: [], count: 0 };
    }
  },

  async getOllamaCategories() {
    try {
      const response = await api.get('/api/ollama/library/categories');
      return response.data;
    } catch (error) {
      console.error('Error getting Ollama categories:', error);
      return { success: false, error: error.message, categories: [] };
    }
  },

  // Chat Operations
  async createChat(title = null, docIds = []) {
    const response = await api.post('/api/chats', { title, doc_ids: docIds });
    return response.data;
  },

  async getChats() {
    const response = await api.get('/api/chats');
    return response.data;
  },

  async getChat(chatId) {
    const response = await api.get(`/api/chats/${chatId}`);
    return response.data;
  },

  async deleteChat(chatId) {
    const response = await api.delete(`/api/chats/${chatId}`);
    return response.data;
  },

  async sendMessage(chatId, message, model = 'llama3.2') {
    const response = await api.post(`/api/chats/${chatId}/messages`, {
      message,
      model,
    });
    return response.data;
  },

  async linkDocument(chatId, docId) {
    const response = await api.post(`/api/chats/${chatId}/documents`, {
      doc_id: docId,
    });
    return response.data;
  },

  async unlinkDocument(chatId, docId) {
    const response = await api.delete(`/api/chats/${chatId}/documents/${docId}`);
    return response.data;
  },

  async getChatDocuments(chatId) {
    const response = await api.get(`/api/chats/${chatId}/documents`);
    return response.data;
  },

  async getChatModels() {
    const response = await api.get('/api/chat/models');
    return response.data;
  },

  async updateChatTitle(chatId, title) {
    const response = await api.patch(`/api/chats/${chatId}/title`, { title });
    return response.data;
  },
};

export default apiService;
