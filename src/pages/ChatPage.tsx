import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChatSidebar, Chat } from '@/components/Chat';
import apiService from '@/utils/api';
import { Chat as ChatType, Document } from '@/types/api';
import Page from '@/components/Page/Page';

export default function ChatPage() {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [chats, setChats] = useState<ChatType[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingChats, setLoadingChats] = useState(false);

  // Load chats and documents on mount
  useEffect(() => {
    loadChats();
    loadDocuments();
  }, []);

  const loadChats = async () => {
    setLoadingChats(true);
    try {
      const result = await apiService.getChats();
      if (result.success) {
        setChats(result.chats || []);
      }
    } catch (err) {
      console.error('Error loading chats:', err);
    } finally {
      setLoadingChats(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const result = await apiService.getDocuments();
      if (result.success) {
        setDocuments(result.documents || []);
      }
    } catch (err) {
      console.error('Error loading documents:', err);
    }
  };

  const handleNewChat = async () => {
    try {
      const result = await apiService.createChat();
      if (result.success) {
        await loadChats();
        navigate(`/chats/${result.chatId}`);
      } else {
        console.error('Create chat failed:', result);
      }
    } catch (err) {
      console.error('Error creating chat:', err);
    }
  };

  const handleSelectChat = (selectedChatId) => {
    navigate(`/chats/${selectedChatId}`);
  };

  const handleDeleteChat = async (deleteChatId) => {
    if (
      !confirm(
        'Are you sure you want to delete this chat? This cannot be undone.'
      )
    )
      return;

    try {
      const result = await apiService.deleteChat(deleteChatId);
      if (result.success) {
        await loadChats();
        if (chatId === deleteChatId) {
          navigate('/chats');
        }
      }
    } catch (err) {
      console.error('Error deleting chat:', err);
    }
  };

  return (
    <Page
      title="Chats"
      subtitle="Chat with your documents privately"
      className="w-full h-full"
    >
      <div className="flex h-full flex-row">
        <ChatSidebar
          chats={chats}
          activeChat={chatId}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          onDeleteChat={handleDeleteChat}
          loading={loadingChats}
        />
        <Chat
          chatId={chatId || ''}
          allDocuments={documents}
          onMessageSent={loadChats}
        />
      </div>
    </Page>
  );
}
