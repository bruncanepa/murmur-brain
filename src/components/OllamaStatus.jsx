import { useState, useEffect } from 'react';
import apiService from '../utils/api';

function OllamaStatus() {
  const [status, setStatus] = useState({ running: false, models: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkStatus();
    // Check status every 10 seconds
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      const result = await apiService.getOllamaStatus();
      setStatus(result);
    } catch (error) {
      console.error('Error checking Ollama status:', error);
      setStatus({ running: false, models: [], error: error.message });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
        <span className="text-sm text-gray-600">Checking...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium text-sm transition-all ${
          status.running
            ? 'bg-success-100 text-success-700'
            : 'bg-error-100 text-error-700'
        }`}
      >
        <div
          className={`w-2 h-2 rounded-full ${
            status.running ? 'bg-success-500 animate-pulse-slow' : 'bg-error-500'
          }`}
        />
        {status.running ? 'AI Ready' : 'AI Offline'}
      </div>
      {status.models.length > 0 && (
        <div className="px-2.5 py-1 bg-primary-100 text-primary-700 rounded-lg text-xs font-semibold">
          {status.models.length} {status.models.length === 1 ? 'model' : 'models'}
        </div>
      )}
    </div>
  );
}

export default OllamaStatus;
