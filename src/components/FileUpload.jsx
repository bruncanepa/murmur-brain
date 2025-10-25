import { useState, useRef } from 'react';
import apiService from '../utils/api';

function FileUpload() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const fileInputRef = useRef(null);

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
        const result = await apiService.uploadDocument(file, (progress) => {
          setUploadProgress((prev) => ({ ...prev, [file.name]: progress }));
        });

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
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden animate-fade-in">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center mb-6">
          <div className="flex-shrink-0 w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div className="ml-4">
            <h2 className="text-xl font-bold text-gray-900">Upload Documents</h2>
            <p className="text-sm text-gray-500">Add files to your knowledge base</p>
          </div>
        </div>

        {/* Drop Zone */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
            dragActive
              ? 'border-primary-500 bg-primary-50 scale-[1.02]'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
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
            <div className="w-16 h-16 mx-auto bg-primary-100 rounded-full flex items-center justify-center">
              {uploading ? (
                <div className="animate-spin">
                  <svg className="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                </div>
              ) : (
                <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              )}
            </div>
            <div>
              <p className="text-base font-medium text-gray-900 mb-1">
                {uploading ? 'Processing files...' : 'Drop files here or click to browse'}
              </p>
              <p className="text-sm text-gray-500">
                Supported: <span className="font-semibold text-gray-700">PDF, CSV, TXT</span> • Max 50MB per file
              </p>
            </div>

            {/* Upload Progress */}
            {Object.keys(uploadProgress).length > 0 && (
              <div className="space-y-2 pt-4">
                {Object.entries(uploadProgress).map(([fileName, progress]) => (
                  <div key={fileName} className="text-left">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 truncate max-w-xs">{fileName}</span>
                      <span className="text-primary-600 font-medium">{progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 animate-slide-up">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Processed Files
                <span className="ml-2 inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                  {files.length}
                </span>
              </h3>
              <button
                onClick={handleClearAll}
                className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors"
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
                    <div className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
                      file.status === 'success' ? 'bg-success-500' : 'bg-error-500'
                    }`}>
                      {file.status === 'success' ? (
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </div>

                    <div className="ml-4 flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 truncate">{file.name}</p>

                      {file.status === 'success' ? (
                        <div className="mt-1 space-y-1">
                          <p className="text-xs text-gray-600">
                            {file.type} • {file.size} MB • {file.chunks} chunks
                          </p>
                          {file.characters && (
                            <p className="text-xs text-gray-600">
                              {file.characters.toLocaleString()} characters • {file.words.toLocaleString()} words
                            </p>
                          )}
                          {file.documentId && (
                            <p className="text-xs text-gray-500 font-mono">ID: {file.documentId.substring(0, 8)}...</p>
                          )}
                        </div>
                      ) : (
                        <p className="mt-1 text-sm text-error-600 font-medium">{file.error}</p>
                      )}
                    </div>

                    <button
                      onClick={() => handleRemoveFile(index)}
                      className="ml-4 flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
