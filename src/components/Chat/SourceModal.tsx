import React, { useEffect, useState } from 'react';
import MarkdownRenderer from './MarkdownRenderer';
import apiService from '../../utils/api';

interface Source {
  vector_id: string;
  file_name: string;
  chunk_index: number;
  similarity: number;
  chunk_text?: string; // Optional - fetched on demand
}

interface SourceModalProps {
  source: Source | null;
  onClose: () => void;
}

const SourceModal: React.FC<SourceModalProps> = ({ source, onClose }) => {
  const [chunkText, setChunkText] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch chunk text when source changes
  useEffect(() => {
    if (!source) {
      setChunkText('');
      setLoading(false);
      setError(null);
      return;
    }

    // If chunk_text already exists (old format), use it
    if (source.chunk_text) {
      setChunkText(source.chunk_text);
      setLoading(false);
      setError(null);
      return;
    }

    // Fetch chunk text from API
    const fetchChunkText = async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await apiService.getVectorContent(source.vector_id);
        if (result.success) {
          setChunkText(result.chunk_text);
        } else {
          setError(result.error || 'Failed to load content');
        }
      } catch (err) {
        setError('Failed to load content');
      } finally {
        setLoading(false);
      }
    };

    fetchChunkText();
  }, [source]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (source) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [source, onClose]);

  if (!source) return null;

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-blue-600 dark:text-blue-400';
    if (score >= 0.4) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[80vh] bg-white dark:bg-gray-900 rounded-lg shadow-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
                {source.file_name}
              </h2>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Chunk {source.chunk_index + 1}</span>
                <span className="text-gray-300 dark:text-gray-600">•</span>
                <span
                  className={`font-medium ${getSimilarityColor(source.similarity)}`}
                >
                  {(source.similarity * 100).toFixed(0)}% similarity
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="flex-shrink-0 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Close modal"
            >
              <svg
                className="w-5 h-5 text-gray-500 dark:text-gray-400"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(80vh-120px)] px-6 py-4">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <span className="ml-3 text-gray-600 dark:text-gray-400">
                  Loading content...
                </span>
              </div>
            )}

            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
                {error}
              </div>
            )}

            {!loading && !error && chunkText && (
              <MarkdownRenderer content={chunkText} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SourceModal;
