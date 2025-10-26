import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import UploadPage from './pages/UploadPage';
import SearchPage from './pages/SearchPage';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import OllamaSetupWizard from './components/Settings/OllamaSetupWizard';
import apiService from './utils/api';
import type { OllamaStatusResponse } from './types/api';
import './App.css';

function App() {
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatusResponse | null>(
    null
  );
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [hasCheckedOnce, setHasCheckedOnce] = useState(false);

  const checkOllamaOnStartup = async () => {
    try {
      const status = await apiService.getOllamaStatus();
      setOllamaStatus(status);

      // Check if user has already dismissed the setup wizard
      const hasDismissed =
        localStorage.getItem('ollama_setup_dismissed') === 'true';

      // Show wizard on first launch if Ollama is not ready and user hasn't dismissed it
      if (!status.ready && !hasDismissed && !hasCheckedOnce) {
        setShowSetupWizard(true);
      }

      setHasCheckedOnce(true);
    } catch (error) {
      console.error('Error checking Ollama status on startup:', error);
      setHasCheckedOnce(true);
    }
  };

  useEffect(() => {
    checkOllamaOnStartup();
  }, []);

  const handleSetupComplete = () => {
    setShowSetupWizard(false);
    checkOllamaOnStartup(); // Refresh status
  };

  const handleSetupSkip = () => {
    setShowSetupWizard(false);
    // Mark as dismissed so it doesn't show again
    localStorage.setItem('ollama_setup_dismissed', 'true');
  };

  return (
    <BrowserRouter>
      <div className="h-screen bg-gray-100 dark:bg-gray-900 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto h-screen">
          <Routes>
            <Route path="/documents" element={<UploadPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/chats/:chatId" element={<ChatPage />} />
            <Route path="/chats" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/chats" replace />} />
          </Routes>
        </main>

        {/* Global Setup Wizard */}
        {showSetupWizard && ollamaStatus && (
          <OllamaSetupWizard
            initialStatus={ollamaStatus}
            onComplete={handleSetupComplete}
            onSkip={handleSetupSkip}
          />
        )}
      </div>
    </BrowserRouter>
  );
}

export default App;
