// API Response Types

export interface HealthCheckResponse {
  status: string;
  message?: string;
}

export interface DocumentMetadata {
  fileName: string;
  fileType: string;
  fileSize: number;
  characterCount: number;
  wordCount: number;
}

export interface UploadProgressEvent {
  phase: 'upload' | 'processing' | 'embedding' | 'complete' | 'error';
  progress: number;
  message: string;
  details?: {
    documentId?: string;
    fileName?: string;
    fileType?: string;
    fileSize?: number;
    characterCount?: number;
    wordCount?: number;
    chunkCount?: number;
  };
}

export interface UploadDocumentResponse {
  success: boolean;
  documentId: string;
  metadata: DocumentMetadata;
  chunkCount: number;
  error?: string;
}

export interface Document {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  character_count: number;
  word_count: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  upload_date: string;
}

export interface DocumentsResponse {
  success?: boolean;
  documents: Document[];
  count: number;
  error?: string;
}

export interface DocumentResponse {
  success?: boolean;
  document: Document;
  error?: string;
}

export interface Stats {
  totalDocuments: number;
  totalChunks: number;
  totalCharacters: number;
  totalWords: number;
}

export interface StatsResponse {
  success?: boolean;
  stats: Stats;
  error?: string;
}

export interface SearchResult {
  document_id: string;
  chunk_id: string;
  content: string;
  similarity: number;
  metadata: {
    file_name: string;
    chunk_index: number;
  };
}

export interface SearchResponse {
  success?: boolean;
  results: SearchResult[];
  query: string;
  count: number;
  error?: string;
}

export interface OllamaModel {
  name: string;
  modified_at?: string;
  size?: number;
  digest?: string;
  details?: {
    format?: string;
    family?: string;
    parameter_size?: string;
    quantization_level?: string;
  };
}

export interface InstallationInstructions {
  platform: string;
  method: string;
  steps: string[];
  download_url: string;
  command?: string;
}

export interface PlatformInfo {
  system: string;
  machine: string;
  platform: string;
}

export interface OllamaStatusResponse {
  success: boolean;
  running: boolean;
  installed: boolean;
  ready: boolean;
  action: 'ready' | 'install_required' | 'start_service';
  message: string;
  installation_instructions?: InstallationInstructions;
  platform?: PlatformInfo;
  error?: string;
}

// Legacy status response for direct Ollama API calls (kept for backward compatibility)
export interface LegacyOllamaStatusResponse {
  running: boolean;
  models: OllamaModel[];
  error?: string;
}

export interface PullModelProgress {
  status: string;
  digest?: string;
  total?: number;
  completed?: number;
}

export interface PullModelResponse {
  success: boolean;
  error?: string;
  cancelled?: boolean;
}

export interface DeleteModelResponse {
  success: boolean;
  error?: string;
}

export interface OllamaLibraryModel {
  name: string;
  description: string;
  tags: string[];
  updated_at: string;
  pulls?: number;
}

export interface OllamaLibrarySearchResponse {
  success: boolean;
  models: OllamaLibraryModel[];
  count: number;
  error?: string;
}

export interface OllamaCategory {
  name: string;
  count: number;
}

export interface OllamaCategoriesResponse {
  success: boolean;
  categories: OllamaCategory[];
  error?: string;
}

export interface Chat {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  model_used?: string;
  sources?: SearchResult[];
}

export interface CreateChatResponse {
  success?: boolean;
  chatId: string;
  title: string | null;
  error?: string;
}

export interface ChatsResponse {
  success?: boolean;
  chats: Chat[];
  count: number;
  error?: string;
}

export interface ChatResponse {
  success?: boolean;
  chat: Chat;
  messages: ChatMessage[];
  error?: string;
}

export interface SendMessageResponse {
  success?: boolean;
  message: ChatMessage;
  response: string;
  context?: SearchResult[];
  sources?: SearchResult[];
  model?: string;
  error?: string;
}

export interface ChatDocumentsResponse {
  success?: boolean;
  documents: Document[];
  count: number;
  error?: string;
}

export interface ChatModelsResponse {
  success?: boolean;
  models: string[];
  error?: string;
}

// API Service Types
export type OnProgressCallback = (event: UploadProgressEvent) => void;
export type OnPullProgressCallback = (progress: PullModelProgress) => void;
