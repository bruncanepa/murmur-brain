import { useState, useEffect } from 'react';
import apiService from '@/utils/api';
import OllamaSetupWizard from './OllamaSetupWizard';
import type { OllamaStatusResponse } from '@/types/api';

function OllamaStatus() {
  const [status, setStatus] = useState<OllamaStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSetupWizard, setShowSetupWizard] = useState(false);

  useEffect(() => {
    checkStatus();
    // Check status every 10 seconds
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      const result = await apiService.getOllamaStatus();
      setStatus(result);
    } catch (error: any) {
      console.error('Error checking Ollama status:', error);
      setStatus({
        success: false,
        running: false,
        installed: false,
        ready: false,
        action: 'install_required',
        message: 'Failed to check Ollama status',
        error: error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSetupComplete = () => {
    setShowSetupWizard(false);
    checkStatus(); // Refresh status
  };

  const handleSetupSkip = () => {
    setShowSetupWizard(false);
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg">
        <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-pulse" />
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Checking...
        </span>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  // Determine UI state based on status
  const getStatusColor = () => {
    if (status.ready) {
      return 'bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-300';
    } else if (status.installed && !status.running) {
      return 'bg-warning-100 dark:bg-warning-900/30 text-warning-700 dark:text-warning-300';
    } else {
      return 'bg-error-100 dark:bg-error-900/30 text-error-700 dark:text-error-300';
    }
  };

  const getStatusIcon = () => {
    if (status.ready) {
      return (
        <div className="w-2 h-2 rounded-full bg-success-500 dark:bg-success-400 animate-pulse-slow" />
      );
    } else if (status.installed && !status.running) {
      return (
        <div className="w-2 h-2 rounded-full bg-warning-500 dark:bg-warning-400" />
      );
    } else {
      return (
        <div className="w-2 h-2 rounded-full bg-error-500 dark:bg-error-400" />
      );
    }
  };

  const getStatusText = () => {
    if (status.ready) {
      return 'AI Ready';
    } else if (status.installed && !status.running) {
      return 'AI Not Running';
    } else {
      return 'AI Not Installed';
    }
  };

  return (
    <>
      <div className="flex items-center gap-2 flex-wrap">
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-medium text-sm transition-all ${getStatusColor()}`}
        >
          {getStatusIcon()}
          {getStatusText()}
        </div>

        {!status.ready && (
          <button
            onClick={() => setShowSetupWizard(true)}
            className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Setup Guide
          </button>
        )}
      </div>

      {showSetupWizard && (
        <OllamaSetupWizard
          initialStatus={status}
          onComplete={handleSetupComplete}
          onSkip={handleSetupSkip}
        />
      )}
    </>
  );
}

export default OllamaStatus;
