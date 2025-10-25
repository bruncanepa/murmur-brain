import { useState, useEffect } from 'react';
import apiService from '../utils/api';

function ModelManager() {
  const [models, setModels] = useState([]);
  const [availableModels] = useState([
    { name: 'llama3.2:latest', description: 'Llama 3.2 - Fast and efficient', size: '~2GB' },
    { name: 'llama3.2:3b', description: 'Llama 3.2 3B - Small and fast', size: '~2GB' },
    { name: 'llama3.1:latest', description: 'Llama 3.1 - Previous generation', size: '~4.7GB' },
    { name: 'mistral:latest', description: 'Mistral - High quality responses', size: '~4.1GB' },
    { name: 'nomic-embed-text:latest', description: 'Text Embeddings (Required for RAG)', size: '~274MB' },
  ]);
  const [selectedModel, setSelectedModel] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const result = await apiService.getOllamaStatus();
      if (result.running) {
        setModels(result.models || []);
      }
    } catch (error) {
      console.error('Error loading models:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadModel = async () => {
    if (!selectedModel) {
      alert('Please select a model to download');
      return;
    }

    try {
      setDownloading(true);
      setProgress({ status: 'Starting download...', percent: 0 });

      const result = await apiService.pullModel(selectedModel, (data) => {
        if (data.status) {
          setProgress({
            status: data.status,
            percent: data.completed && data.total
              ? Math.round((data.completed / data.total) * 100)
              : 0,
          });
        }
      });

      if (result.success) {
        await loadModels();
        setSelectedModel('');
        setProgress(null);
      } else {
        alert(`Download failed: ${result.error}`);
      }
    } catch (error) {
      alert(`Download failed: ${error.message}`);
    } finally {
      setDownloading(false);
    }
  };

  const deleteModel = async (modelName) => {
    if (!confirm(`Are you sure you want to delete ${modelName}?`)) {
      return;
    }

    try {
      const result = await apiService.deleteModel(modelName);
      if (result.success) {
        await loadModels();
      } else {
        alert(`Delete failed: ${result.error}`);
      }
    } catch (error) {
      alert(`Delete failed: ${error.message}`);
    }
  };

  const isModelInstalled = (modelName) => {
    return models.some((m) => m.name === modelName);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden animate-fade-in">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center mb-6">
          <div className="flex-shrink-0 w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div className="ml-4">
            <h2 className="text-xl font-bold text-gray-900">Model Management</h2>
            <p className="text-sm text-gray-500">Download and manage AI models</p>
          </div>
        </div>

        {/* Download Section */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Download New Model
          </label>
          <div className="flex gap-2">
            <select
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={downloading}
            >
              <option value="">Select a model</option>
              {availableModels.map((model) => (
                <option
                  key={model.name}
                  value={model.name}
                  disabled={isModelInstalled(model.name)}
                >
                  {model.name} - {model.description} ({model.size})
                  {isModelInstalled(model.name) ? ' ✓ Installed' : ''}
                </option>
              ))}
            </select>
            <button
              className={`px-6 py-2 rounded-lg font-medium text-white transition-all ${
                downloading || !selectedModel
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700 active:scale-95'
              }`}
              onClick={downloadModel}
              disabled={downloading || !selectedModel}
            >
              {downloading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Downloading
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Progress Display */}
        {progress && (
          <div className="mb-6 p-4 bg-primary-50 border border-primary-200 rounded-lg">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900">Downloading {selectedModel}</p>
                <p className="text-xs text-gray-600">{progress.status}</p>
              </div>
              {progress.percent > 0 && (
                <div className="text-sm font-bold text-primary-600">{progress.percent}%</div>
              )}
            </div>
            {progress.percent > 0 && (
              <div className="w-full bg-primary-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress.percent}%` }}
                />
              </div>
            )}
          </div>
        )}

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center">
            <span className="px-3 bg-white text-sm font-medium text-gray-500">Installed Models</span>
          </div>
        </div>

        {/* Installed Models */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        ) : models.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="text-gray-600 font-medium">No models installed</p>
            <p className="text-sm text-gray-500 mt-1">Download a model to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {models.map((model) => (
              <div
                key={model.name}
                className="flex items-center p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                        model.name.includes('embed')
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-primary-100 text-primary-700'
                      }`}
                    >
                      {model.name.includes('embed') ? 'EMBEDDING' : 'GENERATION'}
                    </span>
                    <span className="font-semibold text-gray-900 truncate">{model.name}</span>
                  </div>
                  <p className="text-sm text-gray-600">
                    {(model.size / 1024 / 1024 / 1024).toFixed(2)} GB
                    {model.modified_at && (
                      <> • Modified {new Date(model.modified_at).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => deleteModel(model.name)}
                  className="ml-4 p-2 text-gray-400 hover:text-error-600 hover:bg-error-50 rounded-lg transition-colors"
                  title="Delete model"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-6 p-4 bg-warning-50 border border-warning-200 rounded-lg flex gap-3">
          <svg className="w-6 h-6 text-warning-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="text-sm text-warning-800">
            <strong>Note:</strong> You need at least one generation model (llama3.2, mistral) and nomic-embed-text for RAG to work properly.
          </div>
        </div>
      </div>
    </div>
  );
}

export default ModelManager;
