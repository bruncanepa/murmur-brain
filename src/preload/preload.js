const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // RAG operations
  queryRag: (query) => ipcRenderer.invoke('query-rag', query),
  uploadFile: (filePath) => ipcRenderer.invoke('upload-file', filePath),

  // Ollama operations
  ollama: {
    getStatus: () => ipcRenderer.invoke('ollama:get-status'),
    checkHealth: () => ipcRenderer.invoke('ollama:check-health'),
    getModels: () => ipcRenderer.invoke('ollama:get-models'),
    pullModel: (modelName) => ipcRenderer.invoke('ollama:pull-model', modelName),
    deleteModel: (modelName) => ipcRenderer.invoke('ollama:delete-model', modelName),
    onPullProgress: (callback) => {
      ipcRenderer.on('ollama:pull-progress', (event, data) => callback(data));
    },
    removePullProgressListener: () => {
      ipcRenderer.removeAllListeners('ollama:pull-progress');
    },
  },
});
