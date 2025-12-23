import { Variable } from '../types';

interface VariableManagerProps {
  variables: Variable[];
  onChange: (variables: Variable[]) => void;
}

export function VariableManager({ variables, onChange }: VariableManagerProps) {
  const updateVariable = (index: number, value: string) => {
    const updated = [...variables];
    updated[index] = { ...updated[index], value };
    onChange(updated);
  };

  if (variables.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
        No variables found in the system prompt. Variables should be in the format: {'{{variableName}}'}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Dynamic Variables</h3>
      <p className="text-sm text-gray-600">
        Update the values for variables used in the system prompt.
      </p>
      <div className="space-y-3">
        {variables.map((variable, index) => (
          <div key={variable.name} className="flex items-center gap-4">
            <label className="w-48 text-sm font-medium text-gray-700">
              {variable.name}:
            </label>
            <input
              type="text"
              value={variable.value}
              onChange={(e) => updateVariable(index, e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={`Enter value for ${variable.name}`}
            />
          </div>
        ))}
      </div>
    </div>
  );
}


