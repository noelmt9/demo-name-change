const API_BASE_URL = 'https://api.vapi.ai';

export class VAPIError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'VAPIError';
  }
}

function getApiKey(): string {
  const key = localStorage.getItem('vapi_api_key');
  if (!key) {
    throw new VAPIError('API key not found. Please set it in the settings.');
  }
  return key;
}

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const apiKey = getApiKey();
  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new VAPIError(
      `API request failed: ${errorText || response.statusText}`,
      response.status
    );
  }

  return response;
}

export async function listAssistants(): Promise<any[]> {
  const response = await fetchWithAuth(`${API_BASE_URL}/assistant`);
  const data = await response.json();
  return Array.isArray(data) ? data : [];
}

export async function getAssistant(id: string): Promise<any> {
  const response = await fetchWithAuth(`${API_BASE_URL}/assistant/${id}`);
  return response.json();
}

export async function updateAssistant(id: string, updates: any): Promise<any> {
  const response = await fetchWithAuth(`${API_BASE_URL}/assistant/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
  return response.json();
}

export function setApiKey(key: string): void {
  localStorage.setItem('vapi_api_key', key);
}

export function getStoredApiKey(): string | null {
  return localStorage.getItem('vapi_api_key');
}


