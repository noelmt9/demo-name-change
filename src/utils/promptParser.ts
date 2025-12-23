import { Variable, FAQ } from '../types';

/**
 * Extract all variables from a system prompt ({{variableName}} format)
 */
export function extractVariables(prompt: string): Variable[] {
  const variablePattern = /\{\{(\w+)\}\}/g;
  const matches = new Set<string>();
  let match;

  while ((match = variablePattern.exec(prompt)) !== null) {
    matches.add(match[1]);
  }

  return Array.from(matches).map(name => ({
    name,
    value: '', // Values will be extracted separately
  }));
}

/**
 * Extract variable values from a prompt by replacing variables with their values
 * and then parsing them back
 */
export function extractVariableValues(prompt: string, variables: Variable[]): Variable[] {
  // This is a simplified approach - in reality, we'd need to track what values
  // were actually set. For now, we'll just return the variable names.
  return variables;
}

/**
 * Replace variables in a prompt with their values
 */
export function replaceVariables(prompt: string, variables: Variable[]): string {
  let result = prompt;
  variables.forEach(({ name, value }) => {
    const regex = new RegExp(`\\{\\{${name}\\}\\}`, 'g');
    result = result.replace(regex, value || `{{${name}}}`);
  });
  return result;
}

/**
 * Extract custom FAQs from the system prompt
 */
export function extractFAQs(prompt: string): FAQ[] {
  const faqs: FAQ[] = [];
  
  // Look for the custom FAQ section
  const customFAQPattern = /### CUSTOM FAQs \(Client-Specific\)\s*\n([\s\S]*?)(?=\n###|\n##|$)/;
  const match = prompt.match(customFAQPattern);
  
  if (!match) {
    return faqs;
  }

  const faqContent = match[1];
  // Parse numbered FAQ entries
  // Pattern matches: "1. If the user asks: "..."\n   - instruction"
  const faqEntryPattern = /(\d+)\.\s*If the user asks:\s*"([^"]+)"\s*\n\s*-\s*([^\n]+)/g;
  let faqMatch;
  let idCounter = 1;

  while ((faqMatch = faqEntryPattern.exec(faqContent)) !== null) {
    faqs.push({
      id: `faq-${idCounter++}`,
      trigger: faqMatch[2],
      instruction: faqMatch[3].trim().replace(/\.$/, ''), // Remove trailing period if present
    });
  }

  return faqs;
}

/**
 * Generate the FAQ block markdown
 */
export function generateFAQBlock(faqs: FAQ[]): string {
  if (faqs.length === 0) {
    return '';
  }

  const faqLines = faqs.map((faq, index) => {
    // Ensure instruction ends with a period
    const instruction = faq.instruction.endsWith('.') ? faq.instruction : `${faq.instruction}.`;
    return `${index + 1}. If the user asks: "${faq.trigger}"\n\n   - ${instruction}`;
  });

  return `### CUSTOM FAQs (Client-Specific)\n\n${faqLines.join('\n\n')}\n`;
}

/**
 * Inject FAQs into the prompt at the correct location
 */
export function injectFAQs(prompt: string, faqs: FAQ[]): string {
  const anchor = '### LOWER PAYMENT FLOW';
  const anchorIndex = prompt.indexOf(anchor);

  if (anchorIndex === -1) {
    // If anchor not found, append at the end
    const faqBlock = generateFAQBlock(faqs);
    return faqs.length > 0 ? `${prompt}\n\n${faqBlock}` : prompt;
  }

  // Remove existing FAQ block if present
  const customFAQPattern = /### CUSTOM FAQs \(Client-Specific\)\s*\n([\s\S]*?)(?=\n###|\n##|$)/;
  let cleanedPrompt = prompt.replace(customFAQPattern, '');

  // Find the anchor again after removal
  const newAnchorIndex = cleanedPrompt.indexOf(anchor);
  
  if (newAnchorIndex === -1) {
    // Fallback: append at end
    const faqBlock = generateFAQBlock(faqs);
    return faqs.length > 0 ? `${cleanedPrompt}\n\n${faqBlock}` : cleanedPrompt;
  }

  // Insert FAQs before the anchor
  const beforeAnchor = cleanedPrompt.substring(0, newAnchorIndex).trimEnd();
  const afterAnchor = cleanedPrompt.substring(newAnchorIndex);
  const faqBlock = generateFAQBlock(faqs);

  if (faqs.length > 0) {
    return `${beforeAnchor}\n\n${faqBlock}\n${afterAnchor}`;
  } else {
    return cleanedPrompt;
  }
}

