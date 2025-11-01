import { useState, useEffect, useCallback } from 'react';
import apiService from '@/utils/api';
import { OllamaStatus } from '@/components/Settings';
import { OllamaModel } from '@/types/api';
import Table, { TableColumn } from '@/components/Table';

function ModelManager() {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);

  // Track currently downloading model name
  const [downloadingModel, setDownloadingModel] = useState<string | null>(null);

  // Abort controller for cancelling downloads
  const [abortController, setAbortController] = useState(null);

  useEffect(() => {
    loadModels();
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const result = await apiService.getOllamaCategories();
      if (result.success) {
        setCategories(result.categories || []);
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const searchModels = useCallback(async (query, category) => {
    try {
      setSearching(true);
      const result = await apiService.searchOllamaLibrary(query, category);
      if (result.success) {
        setSearchResults(result.models || []);
      }
    } catch (error) {
      console.error('Error searching models:', error);
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchQuery || selectedCategory) {
        searchModels(searchQuery, selectedCategory);
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(debounce);
  }, [searchQuery, selectedCategory, searchModels]);

  const stopDownload = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setDownloadingModel(null);
      setDownloading(false);
      setProgress(null);
    }
  };

  const downloadSearchedModel = async (modelName) => {
    try {
      // Create new abort controller
      const controller = new AbortController();
      setAbortController(controller);

      setDownloadingModel(modelName);
      setDownloading(true);
      setProgress({ status: 'Starting download...', percent: 0 });

      const result = await apiService.pullModel(
        modelName,
        (data) => {
          if (data.status) {
            setProgress({
              status: data.status,
              percent:
                data.completed && data.total
                  ? Math.round((data.completed / data.total) * 100)
                  : 0,
            });
          }
        },
        controller.signal
      );

      if (result.success) {
        await loadModels();
        setProgress(null);
        setDownloadingModel(null);
      } else if (result.cancelled) {
        // Download was cancelled, already handled by stopDownload
        console.log('Download cancelled by user');
      } else {
        alert(`Download failed: ${result.error}`);
        setProgress(null);
        setDownloadingModel(null);
      }
    } catch (error) {
      alert(`Download failed: ${error.message}`);
      setProgress(null);
      setDownloadingModel(null);
    } finally {
      setDownloading(false);
      setAbortController(null);
    }
  };

  const loadModels = async () => {
    try {
      setLoading(true);
      const result = await apiService.getInstalledModels();
      if (result.running) {
        setModels(result.models || []);
      }
    } catch (error) {
      console.error('Error loading models:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteModel = async (modelName: string) => {
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

  // Define table columns for installed models
  const modelColumns: TableColumn<OllamaModel>[] = [
    {
      key: 'type',
      header: 'Type',
      render: (model) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
            model.name.includes('embed')
              ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
              : 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
          }`}
        >
          {model.name.includes('embed') ? 'EMBEDDING' : 'GENERATION'}
        </span>
      ),
    },
    {
      key: 'name',
      header: 'Model Name',
      render: (model) => (
        <span className="font-semibold text-gray-900 dark:text-gray-100">
          {model.name}
        </span>
      ),
    },
    {
      key: 'size',
      header: 'Size',
      render: (model) => (
        <span className="text-gray-600 dark:text-gray-400">
          {(model.size / 1024 / 1024 / 1024).toFixed(2)} GB
        </span>
      ),
    },
    {
      key: 'modified',
      header: 'Modified',
      render: (model) => (
        <span className="text-gray-600 dark:text-gray-400">
          {model.modified_at
            ? new Date(model.modified_at).toLocaleDateString()
            : 'N/A'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (model) => (
        <button
          onClick={() => deleteModel(model.name)}
          className="inline-flex items-center justify-center p-2 text-gray-400 dark:text-gray-500 hover:text-error-600 dark:hover:text-error-400 hover:bg-error-50 dark:hover:bg-error-900/20 rounded-lg transition-colors"
          title="Delete model"
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
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      ),
    },
  ];

  return (
    <>
      <OllamaStatus />

      <div className="mt-6">
        {/* Header */}
        <div className="flex items-center mb-6">
          <div className="flex-shrink-0 w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
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
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </div>
          <div className="ml-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Model Management
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Download and manage AI models
            </p>
          </div>
        </div>

        {/* Progress Display */}
        {progress && (
          <div className="mb-6 p-4 bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-primary-600 dark:bg-primary-500 rounded-full flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Downloading {downloadingModel}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {progress.status}
                </p>
              </div>
              {progress.percent > 0 && (
                <div className="text-sm font-bold text-primary-600 dark:text-primary-400">
                  {progress.percent}%
                </div>
              )}
              <button
                onClick={stopDownload}
                className="p-2 text-error-600 dark:text-error-400 hover:bg-error-50 dark:hover:bg-error-900/20 rounded-lg transition-colors"
                title="Stop download"
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            {progress.percent > 0 && (
              <div className="w-full bg-primary-200 dark:bg-primary-900 rounded-full h-2">
                <div
                  className="bg-primary-600 dark:bg-primary-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress.percent}%` }}
                />
              </div>
            )}
          </div>
        )}

        {/* Search Ollama Library */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Search and download models from Ollama Library
          </label>
          <div className="space-y-3">
            {/* Search input and category filter */}
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="Search models (e.g., llama, mistral, phi...)"
                  className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  disabled={downloading}
                />
                <svg
                  className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <select
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                disabled={downloading}
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Search results */}
            {searching && (
              <div className="flex justify-center py-8">
                <div className="w-8 h-8 border-4 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin" />
              </div>
            )}

            {!searching && searchResults.length > 0 && (
              <div className="space-y-2 overflow-y-auto">
                {searchResults.map((model) => (
                  <div
                    key={model.name}
                    className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 transition-all"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                            model.category === 'embedding'
                              ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                              : model.category === 'vision'
                                ? 'bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300'
                                : model.category === 'code'
                                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                                  : 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                          }`}
                        >
                          {model.category.toUpperCase()}
                        </span>
                        <span className="font-semibold text-gray-900 dark:text-gray-100">
                          {model.display_name}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {model.description}
                      </p>
                      {model.size_info && model.size_info.length > 0 ? (
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                            Available sizes (click to download):
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {model.size_info.map((sizeData) => {
                              const modelTag = `${model.name}:${sizeData.param_size}`;
                              const isInstalled = isModelInstalled(modelTag);
                              return (
                                <button
                                  key={sizeData.param_size}
                                  onClick={() =>
                                    downloadSearchedModel(modelTag)
                                  }
                                  disabled={downloading || isInstalled}
                                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium transition-all ${
                                    isInstalled
                                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 cursor-default'
                                      : downloading
                                        ? 'bg-gray-200 dark:bg-gray-600 text-gray-500 cursor-not-allowed'
                                        : 'bg-red-100 dark:bg-red-950/30 text-red-800 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-950/50 cursor-pointer'
                                  }`}
                                  title={
                                    isInstalled
                                      ? 'Already installed'
                                      : `Download ${sizeData.param_size} version (${sizeData.download_size})`
                                  }
                                >
                                  {sizeData.param_size} (
                                  {sizeData.download_size}) {isInstalled && '✓'}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() =>
                            downloadSearchedModel(model.name + ':latest')
                          }
                          disabled={
                            downloading ||
                            isModelInstalled(model.name + ':latest')
                          }
                          className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                            downloading ||
                            isModelInstalled(model.name + ':latest')
                              ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed'
                              : 'bg-primary-600 hover:bg-primary-700 text-white active:scale-95'
                          }`}
                          title={
                            isModelInstalled(model.name + ':latest')
                              ? 'Already installed'
                              : 'Download model'
                          }
                        >
                          {isModelInstalled(model.name + ':latest')
                            ? '✓ Installed'
                            : 'Download'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!searching &&
              (searchQuery || selectedCategory) &&
              searchResults.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No models found matching your search.
                </div>
              )}
          </div>
        </div>

        {/* Divider */}
        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200 dark:border-gray-700" />
          </div>
          <div className="relative flex justify-center">
            <span className="px-3 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400">
              Installed Models
            </span>
          </div>
        </div>

        {/* Installed Models */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-12 h-12 border-4 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin" />
          </div>
        ) : models.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <svg
              className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <p className="text-gray-600 dark:text-gray-400 font-medium">
              No models installed
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
              Download a model to get started
            </p>
          </div>
        ) : (
          <Table
            columns={modelColumns}
            data={models}
            keyExtractor={(model) => model.name}
          />
        )}

        {/* Info Box */}
        <div className="mt-6 p-4 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded-lg flex gap-3">
          <svg
            className="w-6 h-6 text-warning-600 dark:text-warning-400 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div className="text-sm text-warning-800 dark:text-warning-300">
            <strong>Note:</strong> You need at least one generation model
            (llama3.2, mistral) and nomic-embed-text for RAG to work properly.
          </div>
        </div>
      </div>
    </>
  );
}

export default ModelManager;
