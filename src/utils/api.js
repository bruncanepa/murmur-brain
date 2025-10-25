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

    const response = await api.post('/api/documents/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });

    return response.data;
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
    const response = await api.post('/api/search', {
      query,
      top_k: topK,
      threshold,
      doc_ids: docIds,
    });
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

  async pullModel(modelName, onProgress) {
    try {
      const response = await fetch('http://127.0.0.1:11434/api/pull', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: modelName }),
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
};

export default apiService;
