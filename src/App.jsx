import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";
import ChatPage from "./pages/ChatPage";
import SettingsPage from "./pages/SettingsPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="h-screen bg-gray-100 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto h-screen">
          <Routes>
            <Route path="/documents" element={<UploadPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/chats" element={<ChatPage />} />
            <Route path="/chats/:chatId" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/chats" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
