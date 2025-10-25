import { useState } from 'react';
import apiService from '../utils/api';

const Search = () => {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.0);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await apiService.search(query, topK, threshold);
      if (result.success) {
        setResults(result);
      } else {
        setError(result.error || 'Search failed');
      }
    } catch (err) {
      setError(err.message || 'An error occurred during search');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setError(null);
  };

  const getSimilarityColor = (similarity) => {
    if (similarity >= 0.7) return 'bg-success-500 text-success-50';
    if (similarity >= 0.5) return 'bg-warning-500 text-warning-50';
    return 'bg-error-500 text-error-50';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden animate-fade-in">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center mb-6">
          <div className="flex-shrink-0 w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div className="ml-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Semantic Search</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Find relevant content in your documents</p>
          </div>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-6">
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              placeholder="Enter your search query..."
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              className={`px-6 py-3 rounded-lg font-medium text-white transition-all ${
                loading
                  ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700 active:scale-95'
              }`}
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Searching
                </span>
              ) : (
                'Search'
              )}
            </button>
            <button
              type="button"
              className="px-4 py-3 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all"
              onClick={handleClear}
              disabled={loading}
            >
              Clear
            </button>
            <button
              type="button"
              className={`px-4 py-3 rounded-lg transition-all ${
                showSettings
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
              onClick={() => setShowSettings(!showSettings)}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>

          {/* Advanced Settings */}
          {showSettings && (
            <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg space-y-4 animate-slide-up">
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Top Results</label>
                  <span className="text-sm font-medium text-primary-600 dark:text-primary-400">{topK}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Minimum Similarity</label>
                  <span className="text-sm font-medium text-primary-600 dark:text-primary-400">{threshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
              </div>
            </div>
          )}
        </form>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded-lg flex gap-3">
            <svg className="w-6 h-6 text-error-600 dark:text-error-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-error-800 dark:text-error-300 font-medium">{error}</span>
          </div>
        )}

        {/* Search Results */}
        {results && (
          <div>
            {/* Results Summary */}
            <div className="mb-4 p-4 bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    Found <span className="font-bold text-primary-700 dark:text-primary-300">{results.total_matches}</span> matches
                    (showing top <span className="font-bold text-primary-700 dark:text-primary-300">{results.returned}</span>)
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Searched through {results.total_searched} chunks
                  </p>
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                  "{results.query}"
                </div>
              </div>
            </div>

            {/* Results List */}
            {results.results.length === 0 ? (
              <div className="text-center py-16 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-gray-600 dark:text-gray-400 font-medium mb-2">No results found</p>
                <p className="text-sm text-gray-500 dark:text-gray-500">Try different keywords or lower the similarity threshold</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                {results.results.map((result, index) => (
                  <div key={result.vector_id} className="p-4 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all">
                    {/* Result Header */}
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                        <span className="flex items-center justify-center w-8 h-8 bg-primary-600 dark:bg-primary-500 text-white font-bold text-sm rounded-full">
                          {index + 1}
                        </span>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getSimilarityColor(result.similarity)}`}>
                          {(result.similarity * 100).toFixed(1)}% match
                        </span>
                      </div>
                      <div className="text-right text-sm">
                        <p className="font-semibold text-gray-900 dark:text-gray-100 truncate max-w-xs">{result.document.file_name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{result.document.file_type.toUpperCase()}</p>
                      </div>
                    </div>

                    {/* Result Content */}
                    <p className="text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap text-sm mb-3 p-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600">
                      {result.chunk_text}
                    </p>

                    {/* Result Footer */}
                    <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400 pt-3 border-t border-gray-200 dark:border-gray-600">
                      <span>
                        Chunk #{result.chunk_index} • Uploaded {new Date(result.document.upload_date).toLocaleDateString()}
                      </span>
                      <span className="font-mono text-xs">
                        Score: {result.similarity.toFixed(4)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!results && !loading && !error && (
          <div className="text-center py-16">
            <svg className="w-24 h-24 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">Start Searching</h3>
            <p className="text-gray-500 dark:text-gray-400">Enter a query to find relevant content in your documents</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
