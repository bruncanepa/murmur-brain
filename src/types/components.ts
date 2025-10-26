import { Chat, ChatMessage, Document } from './api';

// ChatSidebar Props
export interface ChatSidebarProps {
  chats: Chat[];
  activeChat: string | null;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
  loading: boolean;
}

// Chat Props
export interface ChatProps {
  chatId: string | null;
  allDocuments: Document[];
  onMessageSent?: () => void;
}

// FileUpload Props
export interface FileUploadProps {
  onUploadComplete?: () => void;
}

// Search Props
export interface SearchProps {
  onSearch?: (query: string) => void;
}

// Settings Props
export interface SettingsProps {
  onSettingsChange?: (settings: Record<string, unknown>) => void;
}

// Page Props
export interface PageProps {
  title: string;
  children: React.ReactNode;
}

// Sidebar Props
export interface SidebarProps {
  activePath?: string;
}

// OllamaStatus Props
export interface OllamaStatusProps {
  compact?: boolean;
}

// ModelManager Props
export interface ModelManagerProps {
  onModelChange?: (modelName: string) => void;
}
