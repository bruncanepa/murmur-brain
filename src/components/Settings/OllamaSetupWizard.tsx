import { useState, useEffect, useCallback } from 'react';
import type { OllamaStatusResponse } from '@/types/api';
import apiService from '@/utils/api';

interface OllamaSetupWizardProps {
  initialStatus: OllamaStatusResponse;
  onComplete: () => void;
  onSkip: () => void;
}

function OllamaSetupWizard({
  initialStatus,
  onComplete,
  onSkip,
}: OllamaSetupWizardProps) {
  const [currentStep, setCurrentStep] = useState<
    'welcome' | 'install' | 'waiting' | 'success'
  >('welcome');
  const [status, setStatus] = useState<OllamaStatusResponse>(initialStatus);
  const [copiedCommand, setCopiedCommand] = useState(false);

  // Poll for Ollama installation
  const checkInstallation = useCallback(async () => {
    try {
      const newStatus = await apiService.getOllamaStatus();
      setStatus(newStatus);

      if (newStatus.ready && currentStep === 'waiting') {
        setCurrentStep('success');
        setTimeout(() => {
          onComplete();
        }, 2000);
      }
    } catch (error) {
      console.error('Error checking Ollama status:', error);
    }
  }, [currentStep, onComplete]);

  // Start polling when in waiting state
  useEffect(() => {
    if (currentStep === 'waiting') {
      const interval = setInterval(checkInstallation, 5000);
      return () => clearInterval(interval);
    }
  }, [currentStep, checkInstallation]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCommand(true);
    setTimeout(() => setCopiedCommand(false), 2000);
  };

  const handleNext = () => {
    if (currentStep === 'welcome') {
      setCurrentStep('install');
    } else if (currentStep === 'install') {
      setCurrentStep('waiting');
    }
  };

  const handleOpenDownload = () => {
    if (status.installation_instructions?.download_url) {
      window.open(status.installation_instructions.download_url, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {currentStep === 'welcome' && 'Welcome to Murmur Brain'}
              {currentStep === 'install' && 'Install Ollama'}
              {currentStep === 'waiting' && 'Setting Up...'}
              {currentStep === 'success' && 'All Set!'}
            </h2>
            <button
              onClick={onSkip}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-sm"
            >
              Skip for now
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Welcome Step */}
          {currentStep === 'welcome' && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
                  <svg
                    className="w-10 h-10 text-primary-600 dark:text-primary-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  AI-Powered Document Chat
                </h3>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                  Murmur Brain uses <strong>Ollama</strong> to run AI models
                  locally on your computer. This keeps your documents completely
                  private - no data ever leaves your machine.
                </p>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                  What is Ollama?
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Ollama is a free, open-source tool that runs large language
                  models (LLMs) locally. It powers Murmur Brain's chat and
                  search features.
                </p>
                <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-center gap-2">
                    <svg
                      className="w-4 h-4 text-success-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    100% private - runs offline on your computer
                  </li>
                  <li className="flex items-center gap-2">
                    <svg
                      className="w-4 h-4 text-success-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Free and open source
                  </li>
                  <li className="flex items-center gap-2">
                    <svg
                      className="w-4 h-4 text-success-500"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Supports multiple AI models
                  </li>
                </ul>
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <strong>Note:</strong> You can browse your documents without
                  Ollama, but AI chat and semantic search features will be
                  unavailable.
                </p>
              </div>
            </div>
          )}

          {/* Install Step */}
          {currentStep === 'install' && status.installation_instructions && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Installation Instructions for{' '}
                  {status.installation_instructions.platform}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Follow these steps to install Ollama:
                </p>

                <ol className="space-y-3">
                  {status.installation_instructions.steps.map((step, index) => (
                    <li
                      key={index}
                      className="flex gap-3 text-sm text-gray-700 dark:text-gray-300"
                    >
                      {step.trim() && !step.startsWith('Option') && (
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 flex items-center justify-center text-xs font-semibold">
                          {step.match(/^\d+\./) ? step.match(/^\d+/)?.[0] : '•'}
                        </span>
                      )}
                      <span className={step.trim() ? '' : 'h-2'}>{step}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {status.installation_instructions.command && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Quick Install Command
                  </label>
                  <div className="flex gap-2">
                    <code className="flex-1 bg-gray-900 dark:bg-gray-950 text-gray-100 px-4 py-3 rounded-lg text-sm font-mono overflow-x-auto">
                      {status.installation_instructions.command}
                    </code>
                    <button
                      onClick={() =>
                        copyToClipboard(
                          status.installation_instructions!.command!
                        )
                      }
                      className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium transition-colors"
                    >
                      {copiedCommand ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={handleOpenDownload}
                  className="flex-1 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
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
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                  Download Ollama
                </button>
              </div>
            </div>
          )}

          {/* Waiting Step */}
          {currentStep === 'waiting' && (
            <div className="space-y-6 text-center py-8">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-primary-100 dark:bg-primary-900/30">
                <div className="w-10 h-10 border-4 border-primary-600 dark:border-primary-400 border-t-transparent rounded-full animate-spin" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Waiting for Ollama...
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Once you've installed Ollama, we'll detect it automatically.
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  This wizard will close automatically when Ollama is ready.
                </p>
              </div>

              <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg p-4 text-left">
                <h4 className="font-medium text-red-900 dark:text-red-200 mb-2 flex items-center gap-2">
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                      clipRule="evenodd"
                    />
                  </svg>
                  After installing
                </h4>
                <p className="text-sm text-red-900 dark:text-red-300">
                  {status.action === 'start_service'
                    ? 'Make sure to start the Ollama service. It should start automatically after installation.'
                    : 'Ollama typically starts automatically. If not, launch it from your Applications folder or run `ollama serve` in Terminal.'}
                </p>
              </div>
            </div>
          )}

          {/* Success Step */}
          {currentStep === 'success' && (
            <div className="space-y-6 text-center py-8">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-success-100 dark:bg-success-900/30">
                <svg
                  className="w-10 h-10 text-success-600 dark:text-success-400"
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
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Ollama is Ready!
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  You're all set to start chatting with your documents.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-between">
          <button
            onClick={onSkip}
            className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 font-medium"
          >
            {currentStep === 'waiting' ? 'Close' : 'Skip for now'}
          </button>

          {currentStep !== 'waiting' && currentStep !== 'success' && (
            <button
              onClick={handleNext}
              className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
            >
              {currentStep === 'welcome' ? 'Get Started' : "I've Installed It"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default OllamaSetupWizard;
