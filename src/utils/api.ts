import axios, { AxiosInstance } from 'axios';
import type {
  HealthCheckResponse,
  UploadDocumentResponse,
  DocumentsResponse,
  DocumentResponse,
  StatsResponse,
  SearchResponse,
  OllamaStatusResponse,
  PullModelResponse,
  DeleteModelResponse,
  OllamaLibrarySearchResponse,
  OllamaCategoriesResponse,
  CreateChatResponse,
  ChatsResponse,
  ChatResponse,
  SendMessageResponse,
  ChatDocumentsResponse,
  ChatModelsResponse,
  OnProgressCallback,
  OnPullProgressCallback,
} from '../types/api';

// Auto-detect API URL based on environment
const getApiUrl = (): string => {
  // In development, use localhost
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000';
  }
  // In production (PWA served by Python), API is at same origin
  return window.location.origin;
};

const API_URL = getApiUrl();

// Create axios instance with defaults
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Service
export const apiService = {
  // Health Check
  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await api.get<HealthCheckResponse>('/api/health');
    return response.data;
  },

  // Document Operations
  async uploadDocument(
    file: File,
    onProgress?: OnProgressCallback
  ): Promise<UploadDocumentResponse> {
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
          const uploadPercent = Math.min(
            Math.round((e.loaded / e.total) * 5),
            5
          );
          onProgress({
            phase: 'upload',
            progress: uploadPercent,
            message: 'Uploading file...',
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
                wordCount: lastEventData.details.wordCount,
              },
              chunkCount: lastEventData.details.chunkCount,
            });
          } else if (lastEventData && lastEventData.phase === 'error') {
            reject(new Error(lastEventData.message));
          } else {
            reject(
              new Error('Upload completed but no completion event received')
            );
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

  async getDocuments(): Promise<DocumentsResponse> {
    const response = await api.get<DocumentsResponse>('/api/documents');
    return response.data;
  },

  async getDocument(id: string): Promise<DocumentResponse> {
    const response = await api.get<DocumentResponse>(`/api/documents/${id}`);
    return response.data;
  },

  async deleteDocument(
    id: string
  ): Promise<{ success?: boolean; error?: string }> {
    const response = await api.delete(`/api/documents/${id}`);
    return response.data;
  },

  async getStats(): Promise<StatsResponse> {
    const response = await api.get<StatsResponse>('/api/stats');
    return response.data;
  },

  // Search Operations
  async search(
    query: string,
    topK: number = 5,
    threshold: number = 0.0,
    docIds: string[] | null = null
  ): Promise<SearchResponse> {
    const params: Record<string, string | number> = {
      query,
      top_k: topK,
      threshold,
    };

    // Add doc_ids only if provided (as comma-separated string)
    if (docIds && Array.isArray(docIds) && docIds.length > 0) {
      params.doc_ids = docIds.join(',');
    }

    const response = await api.get<SearchResponse>('/api/search', { params });
    return response.data;
  },

  // Ollama Operations (direct to Ollama API)
  async getOllamaStatus(): Promise<OllamaStatusResponse> {
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

  async pullModel(
    modelName: string,
    onProgress?: OnPullProgressCallback,
    abortSignal: AbortSignal | null = null
  ): Promise<PullModelResponse> {
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

  async deleteModel(modelName: string): Promise<DeleteModelResponse> {
    try {
      const response = await axios.delete('http://127.0.0.1:11434/api/delete', {
        data: { name: modelName },
      });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  async searchOllamaLibrary(
    query: string = '',
    category: string | null = null
  ): Promise<OllamaLibrarySearchResponse> {
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (category) params.append('category', category);

      const response = await api.get(
        `/api/ollama/library/search?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error searching Ollama library:', error);
      return { success: false, error: error.message, models: [], count: 0 };
    }
  },

  async getOllamaCategories(): Promise<OllamaCategoriesResponse> {
    try {
      const response = await api.get('/api/ollama/library/categories');
      return response.data;
    } catch (error) {
      console.error('Error getting Ollama categories:', error);
      return { success: false, error: error.message, categories: [] };
    }
  },

  // Chat Operations
  async createChat(
    title: string | null = null,
    docIds: string[] = []
  ): Promise<CreateChatResponse> {
    const response = await api.post<CreateChatResponse>('/api/chats', {
      title,
      doc_ids: docIds,
    });
    return response.data;
  },

  async getChats(): Promise<ChatsResponse> {
    const response = await api.get<ChatsResponse>('/api/chats');
    return response.data;
  },

  async getChat(chatId: string): Promise<ChatResponse> {
    const response = await api.get<ChatResponse>(`/api/chats/${chatId}`);
    return response.data;
  },

  async deleteChat(
    chatId: string
  ): Promise<{ success?: boolean; error?: string }> {
    const response = await api.delete(`/api/chats/${chatId}`);
    return response.data;
  },

  async sendMessage(
    chatId: string,
    message: string,
    model: string = 'llama3.2'
  ): Promise<SendMessageResponse> {
    const response = await api.post<SendMessageResponse>(
      `/api/chats/${chatId}/messages`,
      {
        message,
        model,
      }
    );
    return response.data;
  },

  async linkDocument(
    chatId: string,
    docId: string
  ): Promise<{ success?: boolean; error?: string }> {
    const response = await api.post(`/api/chats/${chatId}/documents`, {
      doc_id: docId,
    });
    return response.data;
  },

  async unlinkDocument(
    chatId: string,
    docId: string
  ): Promise<{ success?: boolean; error?: string }> {
    const response = await api.delete(
      `/api/chats/${chatId}/documents/${docId}`
    );
    return response.data;
  },

  async getChatDocuments(chatId: string): Promise<ChatDocumentsResponse> {
    const response = await api.get<ChatDocumentsResponse>(
      `/api/chats/${chatId}/documents`
    );
    return response.data;
  },

  async getChatModels(): Promise<ChatModelsResponse> {
    const response = await api.get<ChatModelsResponse>('/api/chat/models');
    return response.data;
  },

  async updateChatTitle(
    chatId: string,
    title: string
  ): Promise<{ success?: boolean; error?: string }> {
    const response = await api.patch(`/api/chats/${chatId}/title`, { title });
    return response.data;
  },
};

export default apiService;
