"""OpenAI API service functions for FAQ prompt generation."""

import requests
from typing import List, Dict, Optional
from config import OPENAI_API_BASE_URL, OPENAI_API_KEY
from utils.prompt_training import build_training_system_prompt, GENERATION_INSTRUCTIONS


def get_api_key() -> Optional[str]:
    """Get OpenAI API key from config."""
    return OPENAI_API_KEY if OPENAI_API_KEY else None


def generate_faq_prompt(
    faqs: List[Dict[str, str]],
    system_prompt_template: Optional[str] = None,
    system_prompt_name: Optional[str] = None
) -> str:
    """
    Generate a prompt from FAQs using OpenAI API with trained writing style.
    
    This function automatically learns from ALL system prompts in prompts/system_prompts/
    to understand the desired writing style, tone, and structure. No prompt selection needed.
    
    Args:
        faqs: List of FAQ dictionaries with 'trigger' and 'instruction' keys
        system_prompt_template: Optional template (deprecated - now uses unified training)
        system_prompt_name: Deprecated - no longer used. All system prompts are used automatically.
    
    Returns:
        Generated prompt string from OpenAI in the trained writing style
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    if not faqs:
        raise ValueError("At least one FAQ is required")
    
    # Use the unified training system prompt (learns from ALL system prompts)
    training_system_prompt = build_training_system_prompt()
    
    # Check if the system prompt is too long (OpenAI has token limits)
    # Rough estimate: 1 token ≈ 4 characters, max context is ~128k tokens for gpt-4o-mini
    # We'll keep system prompt under ~100k tokens to leave room for user prompt and response
    MAX_SYSTEM_PROMPT_LENGTH = 400000  # ~100k tokens
    if len(training_system_prompt) > MAX_SYSTEM_PROMPT_LENGTH:
        # Truncate but keep the important parts (instructions and a sample of examples)
        print(f"Warning: Training system prompt is very long ({len(training_system_prompt)} chars). Truncating...")
        # Keep the first part (instructions) and truncate examples
        parts = training_system_prompt.split("=== WRITING STYLE EXAMPLES ===")
        if len(parts) > 1:
            instructions = parts[0]
            examples = parts[1]
            # Truncate examples to fit
            max_examples_length = MAX_SYSTEM_PROMPT_LENGTH - len(instructions) - 1000
            if len(examples) > max_examples_length:
                examples = examples[:max_examples_length] + "\n\n[... examples truncated for length ...]"
            training_system_prompt = instructions + "=== WRITING STYLE EXAMPLES ===\n" + examples
    
    # Build the FAQ list for the prompt
    faqs_text = "\n".join([
        f"{i+1}. Question the user will ask: \"{faq['trigger']}\"\n   How you want the bot to respond: {faq['instruction']}"
        for i, faq in enumerate(faqs)
    ])
    
    # Use the trained generation instructions
    user_prompt = GENERATION_INSTRUCTIONS.format(faqs=faqs_text)
    
    # Make request to OpenAI with training system prompt
    url = f"{OPENAI_API_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-5.1",  # Using a valid OpenAI model name
        "messages": [
            {
                "role": "system",
                "content": training_system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.1,  # Lower temperature for more consistent style matching
        "max_completion_tokens": 2000  # Increased to handle longer responses
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        # Try to get more detailed error message from response
        error_detail = ""
        try:
            error_response = response.json()
            error_detail = f" - {error_response.get('error', {}).get('message', 'Unknown error')}"
        except:
            error_detail = f" - {response.text[:200]}"
        raise Exception(f"Failed to generate FAQ prompt: {str(e)}{error_detail}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to generate FAQ prompt: {str(e)}")


