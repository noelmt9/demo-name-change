import { useState, useEffect } from 'react';
import { getStoredApiKey, setApiKey } from '../services/vapi';

interface ApiKeyModalProps {
  onClose: () => void;
}

export function ApiKeyModal({ onClose }: ApiKeyModalProps) {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const stored = getStoredApiKey();
    if (stored) {
      setKey(stored);
    }
  }, []);

  const handleSave = () => {
    if (!key.trim()) {
      setError('API key is required');
      return;
    }
    setApiKey(key.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">VAPI API Key</h2>
        <p className="text-gray-600 mb-4">
          Enter your VAPI API key to access your assistants. You can find this in your VAPI dashboard.
        </p>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API Key
          </label>
          <input
            type="password"
            value={key}
            onChange={(e) => {
              setKey(e.target.value);
              setError('');
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your API key"
          />
          {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
        </div>
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}


