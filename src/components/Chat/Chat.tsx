import { useState, useEffect, useRef } from 'react';
import apiService from '../../utils/api';
import { ChatMessage, Document } from '@/types/api';

function Chat({ chatId, allDocuments, onMessageSent }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [linkedDocs, setLinkedDocs] = useState<Document[]>([]);
  const [showDocSelector, setShowDocSelector] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState('llama3.2');
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load chat data when chatId changes
  useEffect(() => {
    if (chatId) {
      loadChat();
      loadLinkedDocuments();
      loadAvailableModels();
    } else {
      setMessages([]);
      setLinkedDocs([]);
      setError(null);
    }
  }, [chatId]);

  const loadChat = async () => {
    try {
      const result = await apiService.getChat(chatId);
      if (result.success) {
        setMessages(result.messages || []);
      }
    } catch (err) {
      console.error('Error loading chat:', err);
    }
  };

  const loadLinkedDocuments = async () => {
    try {
      const result = await apiService.getChatDocuments(chatId);
      if (result.success) {
        setLinkedDocs(result.documents || []);
      }
    } catch (err) {
      console.error('Error loading documents:', err);
    }
  };

  const loadAvailableModels = async () => {
    try {
      const result = await apiService.getChatModels();
      if (result.success && result.models.length > 0) {
        setAvailableModels(result.models);
        // Set first model as default if current model not available
        if (!result.models.includes(selectedModel)) {
          setSelectedModel(result.models[0]);
        }
      }
    } catch (err) {
      console.error('Error loading models:', err);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || loading || !chatId) return;

    if (linkedDocs.length === 0) {
      setError(
        'Please link at least one document to this chat before sending messages.'
      );
      return;
    }

    const userMessage = input.trim();
    setInput('');
    setError(null);
    setLoading(true);

    // Add user message immediately
    const newUserMessage: ChatMessage = {
      id: crypto.randomUUID(),
      chat_id: chatId,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newUserMessage]);

    try {
      const result = await apiService.sendMessage(
        chatId,
        userMessage,
        selectedModel
      );

      if (result.success) {
        // Add assistant response
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          chat_id: chatId,
          role: 'assistant',
          content: result.response,
          sources: result.sources,
          model_used: result.model,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Notify parent to refresh chat list (to update title)
        if (onMessageSent) {
          onMessageSent();
        }
      } else {
        setError(result.error || 'Failed to get response');
      }
    } catch (err) {
      setError('Error sending message: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkDocument = async (docId) => {
    try {
      const result = await apiService.linkDocument(chatId, docId);
      if (result.success) {
        await loadLinkedDocuments();
        setShowDocSelector(false);
      }
    } catch (err) {
      console.error('Error linking document:', err);
    }
  };

  const handleUnlinkDocument = async (docId) => {
    try {
      const result = await apiService.unlinkDocument(chatId, docId);
      if (result.success) {
        await loadLinkedDocuments();
      }
    } catch (err) {
      console.error('Error unlinking document:', err);
    }
  };

  const getSimilarityBadgeColor = (score) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-blue-100 text-blue-800';
    if (score >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (!chatId || chatId === '') {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <svg
            className="w-24 h-24 mx-auto text-gray-300 dark:text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
          <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No chat selected
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Create a new chat or select one from the sidebar
          </p>
        </div>
      </div>
    );
  }

  const unlinkedDocs = allDocuments.filter(
    (doc) => !linkedDocs.some((linked) => linked.id === doc.id)
  );

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Chat
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {linkedDocs.length} documents linked
              </p>
            </div>
          </div>

          {/* Model Selector */}
          {availableModels.length > 0 && (
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {availableModels.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Linked Documents */}
        <div className="mt-3 flex flex-wrap gap-2">
          {linkedDocs.map((doc) => (
            <div
              key={doc.id}
              className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded-full text-sm"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="font-medium">{doc.file_name}</span>
              <button
                onClick={() => handleUnlinkDocument(doc.id)}
                className="text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          ))}

          {/* Add Document Button */}
          <button
            onClick={() => setShowDocSelector(!showDocSelector)}
            className="inline-flex items-center gap-1 px-3 py-1 border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-primary-500 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 rounded-full text-sm transition-all"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add Document
          </button>
        </div>

        {/* Document Selector Dropdown */}
        {showDocSelector && unlinkedDocs.length > 0 && (
          <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg max-h-40 overflow-y-auto">
            {unlinkedDocs.map((doc) => (
              <button
                key={doc.id}
                onClick={() => handleLinkDocument(doc.id)}
                className="w-full text-left px-3 py-2 hover:bg-white dark:hover:bg-gray-600 rounded text-sm transition-all flex items-center gap-2 text-gray-900 dark:text-gray-100"
              >
                <svg
                  className="w-4 h-4 text-gray-400 dark:text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                {doc.file_name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <svg
              className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="text-gray-500 dark:text-gray-400">No messages yet</p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">
              {linkedDocs.length === 0
                ? 'Link documents first, then start chatting'
                : 'Start a conversation by asking a question'}
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                </div>
              )}

              <div
                className={`max-w-2xl ${msg.role === 'user' ? 'order-first' : ''}`}
              >
                <div
                  className={`p-4 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>

                {/* Sources */}
                {msg.role === 'assistant' &&
                  msg.sources &&
                  msg.sources.length > 0 && (
                    <div className="mt-2 space-y-2">
                      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                        Sources:
                      </p>
                      {msg.sources.map((source, sourceIdx) => (
                        <div
                          key={sourceIdx}
                          className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                        >
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <span className="font-medium text-gray-900 dark:text-gray-100">
                              {source.file_name}
                            </span>
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-medium ${getSimilarityBadgeColor(source.similarity)}`}
                            >
                              {(source.similarity * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-gray-600 dark:text-gray-400 text-xs">
                            {source.chunk_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </p>
              </div>

              {msg.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-gray-700 dark:bg-gray-600 rounded-full flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            </div>
            <div className="max-w-2xl">
              <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  Thinking...
                </p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="px-6 pb-2">
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-400">
            {error}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder={
              linkedDocs.length === 0
                ? 'Link documents first...'
                : 'Ask a question about your documents...'
            }
            disabled={loading || linkedDocs.length === 0}
            className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all disabled:bg-gray-100 dark:disabled:bg-gray-800 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !input.trim() || linkedDocs.length === 0}
            className="px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 5l7 7-7 7M5 5l7 7-7 7"
              />
            </svg>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chat;
