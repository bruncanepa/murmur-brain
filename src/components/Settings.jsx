import ModelManager from './ModelManager';
import OllamaStatus from './OllamaStatus';

function Settings() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Settings Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-500 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
              <p className="text-sm text-gray-500">Manage your Local Brain configuration</p>
            </div>
          </div>
          <OllamaStatus />
        </div>
      </div>

      {/* Model Management Section */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4 px-1">Model Management</h2>
        <ModelManager />
      </div>

      {/* Future Settings Sections */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4 px-1">Application Settings</h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-start gap-3 text-gray-500">
            <svg className="w-6 h-6 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-medium text-gray-700 mb-1">Additional settings coming soon</p>
              <p className="text-sm">More configuration options will be available in future updates, including:</p>
              <ul className="text-sm mt-2 space-y-1 list-disc list-inside ml-2">
                <li>Document retention policies</li>
                <li>Search preferences</li>
                <li>Chat history settings</li>
                <li>UI customization</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
