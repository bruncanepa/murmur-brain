import { useState, useEffect, useRef } from 'react';
import apiService from '../utils/api';
import { Document } from '@/types/api';

function FileUpload() {
  const [files, setFiles] = useState([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef(null);

  // Phase display configuration
  const phaseConfig = {
    upload: { label: 'Uploading', color: 'bg-blue-600', icon: '⬆️' },
    validation: { label: 'Validating', color: 'bg-indigo-600', icon: '✓' },
    extraction: { label: 'Extracting', color: 'bg-purple-600', icon: '📄' },
    embedding: {
      label: 'Generating Embeddings',
      color: 'bg-primary-600',
      icon: '🧠',
    },
    storage: { label: 'Saving', color: 'bg-green-600', icon: '💾' },
    complete: { label: 'Complete', color: 'bg-success-600', icon: '✅' },
    error: { label: 'Error', color: 'bg-error-600', icon: '❌' },
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const result = await apiService.getDocuments();
      if (result.success) {
        setDocuments(result.documents || []);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (docId, docName) => {
    if (!confirm(`Are you sure you want to delete "${docName}"?`)) {
      return;
    }

    try {
      const result = await apiService.deleteDocument(docId);
      if (result.success) {
        await loadDocuments();
      } else {
        alert(`Delete failed: ${result.error}`);
      }
    } catch (error) {
      alert(`Delete failed: ${error.message}`);
    }
  };

  const handleFileSelect = (event) => {
    const selectedFiles = Array.from(event.target.files || []);
    if (selectedFiles.length > 0) {
      processFiles(selectedFiles);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files || []);
    if (droppedFiles.length > 0) {
      processFiles(droppedFiles);
    }
  };

  const processFiles = async (fileList) => {
    setUploading(true);

    for (const file of fileList) {
      // Validate file type
      const fileExt = file.name.split('.').pop().toLowerCase();
      if (!['pdf', 'csv', 'txt'].includes(fileExt)) {
        addFileResult({
          name: file.name,
          status: 'error',
          error: `Unsupported file type: ${fileExt}`,
        });
        continue;
      }

      // Validate file size (50MB max)
      if (file.size > 50 * 1024 * 1024) {
        addFileResult({
          name: file.name,
          status: 'error',
          error: 'File too large (max 50MB)',
        });
        continue;
      }

      try {
        const result = await apiService.uploadDocument(
          file,
          (progressData: {
            phase: string;
            progress: number;
            message: string;
            details?: any;
          }) => {
            // progressData: { phase, progress, message, details? }
            setUploadProgress((prev) => ({
              ...prev,
              [file.name]: progressData,
            }));
          }
        );

        if (result.success) {
          addFileResult({
            name: result.metadata.fileName,
            status: 'success',
            type: result.metadata.fileType,
            size: (result.metadata.fileSize / (1024 * 1024)).toFixed(2),
            chunks: result.chunkCount,
            characters: result.metadata.characterCount,
            words: result.metadata.wordCount,
            documentId: result.documentId,
          });
          // Reload documents list after successful upload
          await loadDocuments();
        } else {
          addFileResult({
            name: file.name,
            status: 'error',
            error: result.error || 'Upload failed',
          });
        }
      } catch (error) {
        addFileResult({
          name: file.name,
          status: 'error',
          error: error.message || 'Upload failed',
        });
      }

      // Clear progress for this file
      setUploadProgress((prev) => {
        const updated = { ...prev };
        delete updated[file.name];
        return updated;
      });
    }

    setUploading(false);
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const addFileResult = (fileResult) => {
    setFiles((prev) => [fileResult, ...prev]);
  };

  const handleRemoveFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setFiles([]);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden animate-fade-in">
      <div className="p-6">
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
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          <div className="ml-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Upload Documents
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Add files to your knowledge base
            </p>
          </div>
        </div>

        {/* Drop Zone */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
            dragActive
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 scale-[1.02]'
              : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !uploading && fileInputRef.current?.click()}
          style={{ cursor: uploading ? 'not-allowed' : 'pointer' }}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.csv,.txt"
            onChange={handleFileSelect}
            className="hidden"
            disabled={uploading}
          />

          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
              {uploading ? (
                <div className="animate-spin">
                  <svg
                    className="w-8 h-8 text-primary-600 dark:text-primary-400"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                </div>
              ) : (
                <svg
                  className="w-8 h-8 text-primary-600 dark:text-primary-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              )}
            </div>
            <div>
              <p className="text-base font-medium text-gray-900 dark:text-gray-100 mb-1">
                {uploading
                  ? 'Processing files...'
                  : 'Drop files here or click to browse'}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Supported:{' '}
                <span className="font-semibold text-gray-700 dark:text-gray-300">
                  PDF, CSV, TXT
                </span>{' '}
                • Max 50MB per file
              </p>
            </div>

            {/* Upload Progress */}
            {Object.keys(uploadProgress).length > 0 && (
              <div className="space-y-3 pt-4">
                {Object.entries(uploadProgress).map(
                  ([fileName, progressData]: [
                    string,
                    {
                      phase?: string;
                      progress?: number;
                      message?: string;
                      details?: any;
                    },
                  ]) => {
                    const phase = progressData.phase || 'upload';
                    const progress = progressData.progress || 0;
                    const message = progressData.message || 'Processing...';
                    const config = phaseConfig[phase] || phaseConfig.upload;

                    return (
                      <div
                        key={fileName}
                        className="text-left bg-white rounded-lg p-3 border border-gray-200 shadow-sm"
                      >
                        {/* File name and phase */}
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <span className="text-lg">{config.icon}</span>
                            <span className="text-sm font-semibold text-gray-700 truncate">
                              {fileName}
                            </span>
                          </div>
                          <span className="text-xs font-bold text-gray-900 ml-2">
                            {progress}%
                          </span>
                        </div>

                        {/* Progress bar */}
                        <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2 overflow-hidden">
                          <div
                            className={`${config.color} h-2.5 rounded-full transition-all duration-500 ease-out`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>

                        {/* Phase and message */}
                        <div className="flex items-center justify-between text-xs">
                          <span
                            className={`font-medium ${phase === 'error' ? 'text-error-600' : 'text-gray-600'}`}
                          >
                            {config.label}
                          </span>
                          <span className="text-gray-500 truncate ml-2 max-w-xs">
                            {message}
                          </span>
                        </div>

                        {/* Optional details (batch info) */}
                        {progressData.details && progressData.details.batch && (
                          <div className="mt-1 text-xs text-gray-500">
                            Batch {progressData.details.batch}/
                            {progressData.details.totalBatches}
                          </div>
                        )}
                      </div>
                    );
                  }
                )}
              </div>
            )}
          </div>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 animate-slide-up">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Processed Files
                <span className="ml-2 inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300">
                  {files.length}
                </span>
              </h3>
              <button
                onClick={handleClearAll}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 font-medium transition-colors"
              >
                Clear All
              </button>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
              {files.map((file, index) => (
                <div
                  key={index}
                  className={`relative p-4 rounded-lg border transition-all duration-200 hover:shadow-md ${
                    file.status === 'success'
                      ? 'bg-success-50 border-success-200'
                      : 'bg-error-50 border-error-200'
                  }`}
                >
                  <div className="flex items-start">
                    <div
                      className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                        file.status === 'success'
                          ? 'bg-success-500'
                          : 'bg-error-500'
                      }`}
                    >
                      {file.status === 'success' ? (
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
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      ) : (
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
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      )}
                    </div>

                    <div className="ml-4 flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                        {file.name}
                      </p>

                      {file.status === 'success' ? (
                        <div className="mt-1 space-y-1">
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            {file.type} • {file.size} MB • {file.chunks} chunks
                          </p>
                          {file.characters && (
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {file.characters.toLocaleString()} characters •{' '}
                              {file.words.toLocaleString()} words
                            </p>
                          )}
                          {file.documentId && (
                            <p className="text-xs text-gray-500 dark:text-gray-500 font-mono">
                              ID: {file.documentId.substring(0, 8)}...
                            </p>
                          )}
                        </div>
                      ) : (
                        <p className="mt-1 text-sm text-error-600 dark:text-error-400 font-medium">
                          {file.error}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleRemoveFile(index)}
                      className="ml-4 flex-shrink-0 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
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
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Divider */}
        {files.length > 0 && documents.length > 0 && (
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200 dark:border-gray-700" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-3 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400">
                Your Documents
              </span>
            </div>
          </div>
        )}

        {/* Documents List from Database */}
        <div className={files.length > 0 ? 'mt-6' : 'mt-0'}>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Uploaded Documents
              <span className="ml-2 inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300">
                {documents.length}
              </span>
            </h3>
            {documents.length > 0 && (
              <button
                onClick={loadDocuments}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 font-medium transition-colors flex items-center gap-1"
                title="Refresh list"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Refresh
              </button>
            )}
          </div>

          {loading ? (
            <div className="flex justify-center py-12 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="w-12 h-12 border-4 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin" />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-700">
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
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              <p className="text-gray-600 dark:text-gray-400 font-medium">
                No documents uploaded yet
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                Upload your first document to get started
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="relative p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-700/50 hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0 w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-6 h-6 text-primary-600 dark:text-primary-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>

                    <div className="ml-4 flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                        {doc.file_name || doc.fileName || 'Unknown'}
                      </p>
                      <div className="mt-1 space-y-1">
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {doc.file_type || doc.fileType || 'N/A'} •{' '}
                          {(() => {
                            const size = doc.file_size || doc.fileSize;
                            if (size && !isNaN(size)) {
                              return (size / (1024 * 1024)).toFixed(2);
                            }
                            return '0.00';
                          })()}{' '}
                          MB • {doc.chunk_count || doc.chunkCount || 0} chunks
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          Status:{' '}
                          <span
                            className={`font-medium ${
                              doc.status === 'completed'
                                ? 'text-success-600 dark:text-success-400'
                                : doc.status === 'processing'
                                  ? 'text-warning-600 dark:text-warning-400'
                                  : 'text-error-600 dark:text-error-400'
                            }`}
                          >
                            {doc.status || 'unknown'}
                          </span>
                        </p>
                        {(doc.upload_date || doc.uploadedAt) && (
                          <p className="text-xs text-gray-500 dark:text-gray-500">
                            Uploaded:{' '}
                            {(() => {
                              const dateStr = doc.upload_date || doc.uploadedAt;
                              // Handle SQLite datetime format: "2025-10-25 19:56:47"
                              const date = new Date(dateStr.replace(' ', 'T'));
                              return !isNaN(date.getTime())
                                ? date.toLocaleString()
                                : 'Unknown date';
                            })()}
                          </p>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 font-mono">
                          ID: {doc.id}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() =>
                        handleDeleteDocument(
                          doc.id,
                          doc.file_name || doc.fileName || 'this document'
                        )
                      }
                      className="ml-4 flex-shrink-0 p-2 text-gray-400 dark:text-gray-500 hover:text-error-600 dark:hover:text-error-400 hover:bg-error-50 dark:hover:bg-error-900/20 rounded-lg transition-colors"
                      title="Delete document"
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
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default FileUpload;
