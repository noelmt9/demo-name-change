import { useState, useEffect } from 'react';
import { listAssistants, getAssistant, updateAssistant, getStoredApiKey, VAPIError } from './services/vapi';
import { extractVariables, replaceVariables, extractFAQs, injectFAQs } from './utils/promptParser';
import { Variable, FAQ, VAPIAssistant } from './types';
import { ApiKeyModal } from './components/ApiKeyModal';
import { VariableManager } from './components/VariableManager';
import { FAQManager } from './components/FAQManager';

function App() {
  const [apiKeyModalOpen, setApiKeyModalOpen] = useState(false);
  const [assistants, setAssistants] = useState<any[]>([]);
  const [selectedAssistantId, setSelectedAssistantId] = useState<string>('');
  const [assistant, setAssistant] = useState<VAPIAssistant | null>(null);
  const [variables, setVariables] = useState<Variable[]>([]);
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [systemPrompt, setSystemPrompt] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  useEffect(() => {
    // Check for API key on mount
    if (!getStoredApiKey()) {
      setApiKeyModalOpen(true);
    } else {
      loadAssistants();
    }
  }, []);

  useEffect(() => {
    if (selectedAssistantId) {
      loadAssistant(selectedAssistantId);
    } else {
      setAssistant(null);
      setVariables([]);
      setFaqs([]);
      setSystemPrompt('');
    }
  }, [selectedAssistantId]);

  const loadAssistants = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await listAssistants();
      setAssistants(data);
    } catch (err) {
      if (err instanceof VAPIError && err.status === 401) {
        setApiKeyModalOpen(true);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load assistants');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadAssistant = async (id: string) => {
    try {
      setLoading(true);
      setError('');
      const data = await getAssistant(id);
      setAssistant(data);

      // Extract system prompt
      const prompt = data?.model?.messages?.[0]?.content || '';
      setSystemPrompt(prompt);

      // Extract variables
      const vars = extractVariables(prompt);
      setVariables(vars);

      // Extract FAQs
      const extractedFAQs = extractFAQs(prompt);
      setFaqs(extractedFAQs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assistant');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedAssistantId || !assistant) {
      setError('Please select an assistant first');
      return;
    }

    try {
      setSaving(true);
      setError('');
      setSuccess('');

      // Replace variables in the prompt
      let updatedPrompt = replaceVariables(systemPrompt, variables);

      // Inject FAQs
      updatedPrompt = injectFAQs(updatedPrompt, faqs);

      // Update the assistant
      await updateAssistant(selectedAssistantId, {
        model: {
          messages: [
            {
              role: 'system',
              content: updatedPrompt,
            },
          ],
        },
      });

      setSuccess('Assistant updated successfully!');
      
      // Reload the assistant to reflect changes
      await loadAssistant(selectedAssistantId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save assistant');
    } finally {
      setSaving(false);
    }
  };

  const handleApiKeySaved = () => {
    setApiKeyModalOpen(false);
    loadAssistants();
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {apiKeyModalOpen && (
        <ApiKeyModal onClose={handleApiKeySaved} />
      )}

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">VAPI Assistant Manager</h1>
              <p className="text-gray-600 mt-1">Manage your voice assistant configurations</p>
            </div>
            <button
              onClick={() => setApiKeyModalOpen(true)}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Settings
            </button>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Assistant
            </label>
            <select
              value={selectedAssistantId}
              onChange={(e) => setSelectedAssistantId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="">-- Select an assistant --</option>
              {assistants.map((asst) => (
                <option key={asst.id} value={asst.id}>
                  {asst.name || asst.id}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md text-green-700">
              {success}
            </div>
          )}

          {loading && (
            <div className="text-center py-8 text-gray-500">
              Loading...
            </div>
          )}

          {!loading && selectedAssistantId && assistant && (
            <div className="space-y-8">
              <div className="border-t pt-6">
                <VariableManager
                  variables={variables}
                  onChange={setVariables}
                />
              </div>

              <div className="border-t pt-6">
                <FAQManager
                  faqs={faqs}
                  onChange={setFaqs}
                />
              </div>

              <div className="border-t pt-6">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="w-full px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed font-medium"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          {!loading && !selectedAssistantId && (
            <div className="text-center py-12 text-gray-500">
              Select an assistant to begin managing its configuration
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;


