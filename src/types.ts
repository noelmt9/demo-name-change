export interface VAPIAssistant {
  id: string;
  name?: string;
  model?: {
    messages?: Array<{
      role: string;
      content: string;
    }>;
  };
  [key: string]: any;
}

export interface Variable {
  name: string;
  value: string;
}

export interface FAQ {
  id: string;
  trigger: string;
  instruction: string;
}

export interface AssistantConfig {
  assistant: VAPIAssistant;
  variables: Variable[];
  faqs: FAQ[];
  systemPrompt: string;
}


