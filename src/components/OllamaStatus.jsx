import { useState, useEffect } from 'react';

function OllamaStatus() {
  const [status, setStatus] = useState(null);
  const [isHealthy, setIsHealthy] = useState(false);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState('');

  useEffect(() => {
    checkStatus();
    loadModels();

    // Set up progress listener
    window.electronAPI.ollama.onPullProgress((data) => {
      setDownloadProgress(data.progress?.status || 'Downloading...');
    });

    // Check health every 10 seconds
    const interval = setInterval(() => {
      checkHealth();
    }, 10000);

    return () => {
      clearInterval(interval);
      window.electronAPI.ollama.removePullProgressListener();
    };
  }, []);

  const checkStatus = async () => {
    try {
      const statusData = await window.electronAPI.ollama.getStatus();
      setStatus(statusData);
      await checkHealth();
    } catch (error) {
      console.error('Error checking status:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkHealth = async () => {
    try {
      const healthy = await window.electronAPI.ollama.checkHealth();
      setIsHealthy(healthy);
    } catch (error) {
      console.error('Error checking health:', error);
      setIsHealthy(false);
    }
  };

  const loadModels = async () => {
    try {
      const modelList = await window.electronAPI.ollama.getModels();
      setModels(modelList);
    } catch (error) {
      console.error('Error loading models:', error);
    }
  };

  const handleDownloadModel = async () => {
    if (!selectedModel.trim()) return;

    setDownloading(true);
    setDownloadProgress('Starting download...');

    try {
      const result = await window.electronAPI.ollama.pullModel(selectedModel);
      if (result.success) {
        setDownloadProgress('Download complete!');
        await loadModels();
        setSelectedModel('');
        setTimeout(() => {
          setDownloadProgress('');
          setDownloading(false);
        }, 2000);
      } else {
        setDownloadProgress(`Error: ${result.error}`);
        setDownloading(false);
      }
    } catch (error) {
      console.error('Error downloading model:', error);
      setDownloadProgress(`Error: ${error.message}`);
      setDownloading(false);
    }
  };

  const handleDeleteModel = async (modelName) => {
    if (!confirm(`Are you sure you want to delete ${modelName}?`)) return;

    try {
      const success = await window.electronAPI.ollama.deleteModel(modelName);
      if (success) {
        await loadModels();
      }
    } catch (error) {
      console.error('Error deleting model:', error);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-gray-600">Loading Ollama status...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">Ollama Status</h2>

      {/* Status Indicator */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isHealthy ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="font-medium">
            {isHealthy ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        {status && (
          <div className="mt-2 text-sm text-gray-600">
            <p>Server: {status.baseUrl}</p>
            <p>Status: {status.isRunning ? 'Running' : 'Stopped'}</p>
          </div>
        )}
      </div>

      {/* Model Download */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">Download Model</h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            placeholder="Model name (e.g., llama3.2, nomic-embed-text)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={downloading}
          />
          <button
            onClick={handleDownloadModel}
            disabled={downloading || !selectedModel.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {downloading ? 'Downloading...' : 'Download'}
          </button>
        </div>
        {downloadProgress && (
          <p className="mt-2 text-sm text-gray-600">{downloadProgress}</p>
        )}
        <div className="mt-2 text-sm text-gray-500">
          <p>Popular models:</p>
          <ul className="list-disc list-inside">
            <li>llama3.2 - Latest Llama model (chat)</li>
            <li>llama3.2:1b - Smaller Llama model</li>
            <li>nomic-embed-text - Embeddings model</li>
            <li>mistral - Mistral chat model</li>
          </ul>
        </div>
      </div>

      {/* Installed Models */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Installed Models</h3>
        {models.length === 0 ? (
          <p className="text-gray-600">No models installed yet</p>
        ) : (
          <div className="space-y-2">
            {models.map((model) => (
              <div
                key={model.name}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
              >
                <div>
                  <p className="font-medium">{model.name}</p>
                  {model.size && (
                    <p className="text-sm text-gray-600">
                      Size: {(model.size / 1024 / 1024 / 1024).toFixed(2)} GB
                    </p>
                  )}
                </div>
                <button
                  onClick={() => handleDeleteModel(model.name)}
                  className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default OllamaStatus;
