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
    existing_prompt: Optional[str] = None,
    system_prompt_template: Optional[str] = None,
    system_prompt_name: Optional[str] = None
) -> str:
    """
    Generate a prompt from FAQs using OpenAI API with trained writing style.
    
    This function uses training examples from prompts/training_examples/ to learn
    the desired writing style, tone, and nested structure. It also considers the
    existing system prompt to extract available flows and existing FAQ sections.
    
    Args:
        faqs: List of FAQ dictionaries with 'trigger' and 'instruction' keys
        existing_prompt: Optional existing system prompt to extract flows and FAQ context from
        system_prompt_template: Optional template (deprecated - not used)
        system_prompt_name: Deprecated - not used
    
    Returns:
        Generated prompt string from OpenAI in the trained writing style
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    if not faqs:
        raise ValueError("At least one FAQ is required")
    
    # Use the unified training system prompt (learns from training examples only)
    training_system_prompt = build_training_system_prompt()
    
    # Extract context from existing prompt if provided
    from utils.prompt_parser import extract_flows, extract_existing_faq_section, count_existing_faqs
    
    available_flows = []
    existing_faqs = ""
    existing_faq_count = 0
    
    if existing_prompt:
        available_flows = extract_flows(existing_prompt)
        existing_faqs = extract_existing_faq_section(existing_prompt)
        existing_faq_count = count_existing_faqs(existing_prompt)
    
    # Format available flows for the prompt
    if available_flows:
        flows_text = "\n".join([f"- {flow}" for flow in available_flows])
    else:
        flows_text = "No specific flows found in the existing prompt. Use common flows like 'TRANSFER FLOW' or 'MAKE PAYMENT FLOW' only if contextually appropriate, otherwise prefer returning to the current step."
    
    # Format existing FAQs
    if existing_faqs:
        existing_faqs_text = existing_faqs[:2000]  # Limit to 2000 chars to avoid token limits
        if len(existing_faqs) > 2000:
            existing_faqs_text += "\n\n[... existing FAQs continue ...]"
    else:
        existing_faqs_text = "No existing FAQ section found. This will be the first FAQ section."
    
    # Build the FAQ list for the prompt
    faqs_text = "\n".join([
        f"{i+1}. Question the user will ask: \"{faq['trigger']}\"\n   How you want the bot to respond: {faq['instruction']}"
        for i, faq in enumerate(faqs)
    ])
    
    # Use the trained generation instructions with context
    # Adjust numbering if there are existing FAQs
    if existing_faq_count > 0:
        # Update the instructions to continue numbering
        generation_instructions = GENERATION_INSTRUCTIONS.replace(
            "Number your FAQs starting from 1",
            f"Number your FAQs starting from {existing_faq_count + 1} (there are already {existing_faq_count} existing FAQs)"
        )
    else:
        generation_instructions = GENERATION_INSTRUCTIONS
    
    user_prompt = generation_instructions.format(
        available_flows=flows_text,
        existing_faqs=existing_faqs_text,
        faqs=faqs_text
    )
    
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


