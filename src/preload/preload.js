const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  queryRag: (query) => ipcRenderer.invoke('query-rag', query),
  uploadFile: (filePath) => ipcRenderer.invoke('upload-file', filePath),
  downloadModel: (modelName) => ipcRenderer.invoke('download-model', modelName),
  getInstalledModels: () => ipcRenderer.invoke('get-installed-models'),
});
