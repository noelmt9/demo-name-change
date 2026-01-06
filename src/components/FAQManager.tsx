import { useState } from 'react';
import { FAQ } from '../types';

interface FAQManagerProps {
  faqs: FAQ[];
  onChange: (faqs: FAQ[]) => void;
}

export function FAQManager({ faqs, onChange }: FAQManagerProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newFAQ, setNewFAQ] = useState({ trigger: '', instruction: '' });

  const handleAdd = () => {
    if (!newFAQ.trigger.trim() || !newFAQ.instruction.trim()) {
      return;
    }
    const faq: FAQ = {
      id: `faq-${Date.now()}`,
      trigger: newFAQ.trigger.trim(),
      instruction: newFAQ.instruction.trim(),
    };
    onChange([...faqs, faq]);
    setNewFAQ({ trigger: '', instruction: '' });
    setShowAddForm(false);
  };

  const handleEdit = (id: string, updates: Partial<FAQ>) => {
    onChange(faqs.map(faq => faq.id === id ? { ...faq, ...updates } : faq));
    setEditingId(null);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this FAQ?')) {
      onChange(faqs.filter(faq => faq.id !== id));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-black">Custom FAQs</h3>
          <p className="text-sm text-black">
            Manage custom FAQ entries that will be injected into the system prompt.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="px-4 py-2 btn-gradient text-white rounded-md"
        >
          + Add FAQ
        </button>
      </div>

      {showAddForm && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              User Trigger
            </label>
            <input
              type="text"
              value={newFAQ.trigger}
              onChange={(e) => setNewFAQ({ ...newFAQ, trigger: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#2D83C5]"
              placeholder="What the user might say..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-black mb-1">
              Bot Response Instruction
            </label>
            <textarea
              value={newFAQ.instruction}
              onChange={(e) => setNewFAQ({ ...newFAQ, instruction: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#2D83C5]"
              rows={2}
              placeholder="How the bot should respond..."
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Save
            </button>
            <button
              onClick={() => {
                setShowAddForm(false);
                setNewFAQ({ trigger: '', instruction: '' });
              }}
              className="px-4 py-2 text-black border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {faqs.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-4 text-center text-black">
            No custom FAQs yet. Click "Add FAQ" to create one.
          </div>
        ) : (
          faqs.map((faq) => (
            <div key={faq.id} className="border border-gray-200 rounded-lg p-4">
              {editingId === faq.id ? (
                <EditFAQForm
                  faq={faq}
                  onSave={(updates) => handleEdit(faq.id, updates)}
                  onCancel={() => setEditingId(null)}
                />
              ) : (
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <p className="font-medium text-black">
                        If user asks: "{faq.trigger}"
                      </p>
                      <p className="text-sm text-black mt-1">
                        → {faq.instruction}
                      </p>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => setEditingId(faq.id)}
                        className="px-3 py-1 text-sm text-[#2D83C5] hover:text-[#010066]"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(faq.id)}
                        className="px-3 py-1 text-sm text-red-600 hover:text-red-700"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

interface EditFAQFormProps {
  faq: FAQ;
  onSave: (updates: Partial<FAQ>) => void;
  onCancel: () => void;
}

function EditFAQForm({ faq, onSave, onCancel }: EditFAQFormProps) {
  const [trigger, setTrigger] = useState(faq.trigger);
  const [instruction, setInstruction] = useState(faq.instruction);

  const handleSave = () => {
    if (!trigger.trim() || !instruction.trim()) {
      return;
    }
    onSave({ trigger: trigger.trim(), instruction: instruction.trim() });
  };

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-black mb-1">
          User Trigger
        </label>
        <input
          type="text"
          value={trigger}
          onChange={(e) => setTrigger(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#2D83C5]"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-black mb-1">
          Bot Response Instruction
        </label>
        <textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#2D83C5]"
          rows={2}
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          Save
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 text-black border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}


