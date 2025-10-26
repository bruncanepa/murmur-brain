import { spawn, ChildProcess } from 'child_process';
import axios from 'axios';
// import { app } from 'electron'; // Disabled for browser build
import path from 'path';

class OllamaService {
  private ollamaProcess: ChildProcess | null;
  private baseUrl: string;
  private isRunning: boolean;
  private ollamaPath: string;

  constructor() {
    this.ollamaProcess = null;
    this.baseUrl = 'http://localhost:11434';
    this.isRunning = false;
    this.ollamaPath = '/usr/local/bin/ollama'; // Default Mac path
  }

  /**
   * Start the Ollama server
   */
  async start() {
    if (this.isRunning) {
      console.log('Ollama server is already running');
      return true;
    }

    try {
      // Check if Ollama is already running (started externally)
      const isAlreadyRunning = await this.checkHealth();
      if (isAlreadyRunning) {
        console.log('Ollama server is already running externally');
        this.isRunning = true;
        return true;
      }

      console.log('Starting Ollama server...');

      // Set OLLAMA_MODELS to app user data directory
      const modelsPath = path.join(app.getPath('userData'), 'models');

      // Start Ollama serve process
      this.ollamaProcess = spawn(this.ollamaPath, ['serve'], {
        env: {
          ...process.env,
          OLLAMA_MODELS: modelsPath,
          OLLAMA_HOST: '127.0.0.1:11434',
        },
        detached: false,
      });

      this.ollamaProcess.stdout?.on('data', (data) => {
        console.log(`Ollama: ${data}`);
      });

      this.ollamaProcess.stderr?.on('data', (data) => {
        console.error(`Ollama error: ${data}`);
      });

      this.ollamaProcess.on('error', (error) => {
        console.error('Failed to start Ollama:', error);
        this.isRunning = false;
      });

      this.ollamaProcess.on('exit', (code, signal) => {
        console.log(
          `Ollama process exited with code ${code} and signal ${signal}`
        );
        this.isRunning = false;
        this.ollamaProcess = null;
      });

      // Wait for server to be ready
      const serverReady = await this.waitForServer(30000); // 30 second timeout
      if (serverReady) {
        this.isRunning = true;
        console.log('Ollama server started successfully');
        return true;
      } else {
        console.error('Ollama server failed to start within timeout');
        this.stop();
        return false;
      }
    } catch (error) {
      console.error('Error starting Ollama:', error);
      return false;
    }
  }

  /**
   * Stop the Ollama server
   */
  stop() {
    if (this.ollamaProcess) {
      console.log('Stopping Ollama server...');
      this.ollamaProcess.kill();
      this.ollamaProcess = null;
    }
    this.isRunning = false;
  }

  /**
   * Wait for Ollama server to be ready
   */
  async waitForServer(timeout = 30000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      const isHealthy = await this.checkHealth();
      if (isHealthy) {
        return true;
      }
      // Wait 500ms before next check
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    return false;
  }

  /**
   * Check if Ollama server is healthy
   */
  async checkHealth() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/tags`, {
        timeout: 2000,
      });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get list of installed models
   */
  async getModels() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/tags`);
      return response.data.models || [];
    } catch (error) {
      console.error('Error getting models:', error);
      return [];
    }
  }

  /**
   * Pull/download a model
   */
  async pullModel(modelName, onProgress) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/pull`,
        { name: modelName },
        {
          responseType: 'stream',
          timeout: 0, // No timeout for model downloads
        }
      );

      return new Promise((resolve, reject) => {
        let lastProgress = '';

        response.data.on('data', (chunk) => {
          const lines = chunk
            .toString()
            .split('\n')
            .filter((line) => line.trim());
          lines.forEach((line) => {
            try {
              const data = JSON.parse(line);
              if (onProgress) {
                onProgress(data);
              }
              lastProgress = data.status || '';
            } catch (e) {
              // Ignore parse errors
            }
          });
        });

        response.data.on('end', () => {
          resolve({ success: true, status: lastProgress });
        });

        response.data.on('error', (error) => {
          reject(error);
        });
      });
    } catch (error) {
      console.error('Error pulling model:', error);
      throw error;
    }
  }

  /**
   * Delete a model
   */
  async deleteModel(modelName) {
    try {
      await axios.delete(`${this.baseUrl}/api/delete`, {
        data: { name: modelName },
      });
      return true;
    } catch (error) {
      console.error('Error deleting model:', error);
      return false;
    }
  }

  /**
   * Get server status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      baseUrl: this.baseUrl,
      ollamaPath: this.ollamaPath,
    };
  }
}

// Export singleton instance
export default new OllamaService();
