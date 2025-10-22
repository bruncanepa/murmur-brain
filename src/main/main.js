const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const ollamaService = require('../services/ollama-service');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, '../preload/preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  // Start Ollama server
  console.log('Starting Ollama service...');
  const ollamaStarted = await ollamaService.start();
  if (ollamaStarted) {
    console.log('Ollama service started successfully');
  } else {
    console.warn('Ollama service failed to start - some features may not work');
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Stop Ollama server when app quits
  console.log('Stopping Ollama service...');
  ollamaService.stop();
});

// Ollama IPC handlers
ipcMain.handle('ollama:get-status', async () => {
  return ollamaService.getStatus();
});

ipcMain.handle('ollama:check-health', async () => {
  return await ollamaService.checkHealth();
});

ipcMain.handle('ollama:get-models', async () => {
  return await ollamaService.getModels();
});

ipcMain.handle('ollama:pull-model', async (event, modelName) => {
  try {
    const result = await ollamaService.pullModel(modelName, (progress) => {
      // Send progress updates to renderer
      mainWindow?.webContents.send('ollama:pull-progress', {
        modelName,
        progress,
      });
    });
    return { success: true, result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('ollama:delete-model', async (event, modelName) => {
  return await ollamaService.deleteModel(modelName);
});

// RAG IPC handlers
ipcMain.handle('query-rag', async (event, query) => {
  // Placeholder for RAG query handling
  return 'RAG query handler not yet implemented';
});
