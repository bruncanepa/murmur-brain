import { useState } from 'react';
import Sidebar from './components/Sidebar';
import FileUpload from './components/FileUpload';
import Search from './components/Search';
import Settings from './components/Settings';
import './App.css';

function App() {
  const [activeView, setActiveView] = useState('upload');
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const handleQuery = async () => {
    if (message.trim()) {
      try {
        // TODO: Implement RAG query in Phase 6
        setResponse('RAG query system will be implemented in Phase 6. For now, use the Search tab to find relevant content in your documents.');
      } catch (error) {
        setResponse('Error: ' + error.message);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <Sidebar activeView={activeView} onViewChange={setActiveView} />

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {activeView === 'upload' && <FileUpload />}
          {activeView === 'search' && <Search />}
          {activeView === 'settings' && <Settings />}
          {activeView === 'chat' && (
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden animate-fade-in">
              <div className="p-6">
                <div className="flex items-center mb-6">
                  <div className="flex-shrink-0 w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <h2 className="text-xl font-bold text-gray-900">Ask Questions</h2>
                    <p className="text-sm text-gray-500">Chat with your documents</p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
                    placeholder="Ask a question about your documents..."
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
                  />
                  <button
                    onClick={handleQuery}
                    className="px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 active:scale-95 transition-all flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                    Ask
                  </button>
                </div>

                {response && (
                  <div className="mt-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
                    <div className="flex gap-3">
                      <svg className="w-6 h-6 text-primary-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div>
                        <h3 className="font-semibold text-primary-900 mb-1">Response:</h3>
                        <p className="text-sm text-primary-800">{response}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
