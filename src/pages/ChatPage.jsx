import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ChatSidebar from '../components/ChatSidebar';
import Chat from '../components/Chat';
import apiService from '../utils/api';

export default function ChatPage() {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [chats, setChats] = useState([]);
  const [documents, setDocuments] = useState([]);
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
    console.log('New chat button clicked');
    try {
      console.log('Calling createChat API...');
      const result = await apiService.createChat();
      console.log('Create chat result:', result);
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
    if (!confirm('Are you sure you want to delete this chat? This cannot be undone.')) return;

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
    <div className="h-screen flex">
      <ChatSidebar
        chats={chats}
        activeChat={chatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        loading={loadingChats}
      />
      <Chat chatId={chatId || ''} allDocuments={documents} />
    </div>
  );
}
