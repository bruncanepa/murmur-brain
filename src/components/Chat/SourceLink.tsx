import { SearchResult } from '@/types/api';
import React from 'react';

interface SourceLinkProps {
  source: SearchResult;
  onClick: () => void;
}

const SourceLink: React.FC<SourceLinkProps> = ({ source, onClick }) => {
  const getSimilarityBadgeColor = (score: number) => {
    if (score >= 0.8)
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
    if (score >= 0.6)
      return 'bg-red-100 text-red-900 dark:bg-red-950/30 dark:text-red-400';
    if (score >= 0.4)
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
  };

  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 text-sm text-left hover:underline text-red-700 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 transition-colors"
    >
      <span className="font-medium truncate max-w-xs">{source.file_name}</span>
      <span
        className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${getSimilarityBadgeColor(source.similarity)}`}
      >
        {(source.similarity * 100).toFixed(0)}%
      </span>
      <span className="text-gray-400 dark:text-gray-600 flex-shrink-0">|</span>
      <span className="text-gray-600 dark:text-gray-400 flex-shrink-0">
        Chunk {source.chunk_index + 1}
      </span>
    </button>
  );
};

export default SourceLink;
