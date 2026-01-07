"""OpenAI API service functions for FAQ prompt generation."""

import requests
import random
import json
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from config import OPENAI_API_BASE_URL, OPENAI_API_KEY, GENERATION_MODEL
from utils.prompt_training import build_training_system_prompt, GENERATION_INSTRUCTIONS, load_writing_style_examples


def get_api_key() -> Optional[str]:
    """Get OpenAI API key from config."""
    return OPENAI_API_KEY if OPENAI_API_KEY else None


def generate_faq_prompt(
    faqs: List[Dict[str, str]],
    existing_prompt: Optional[str] = None,
    system_prompt_template: Optional[str] = None,
    system_prompt_name: Optional[str] = None,
    exclude_training_indices: Optional[List[int]] = None
) -> Tuple[str, List[int]]:
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
        exclude_training_indices: Optional list of training example indices to exclude
    
    Returns:
        Tuple of (generated prompt string, list of training example indices that were used)
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    if not faqs:
        raise ValueError("At least one FAQ is required")
    
    # Determine which training examples to use
    all_examples = load_writing_style_examples()
    total_examples = len(all_examples)
    
    if total_examples == 0:
        raise ValueError("No training examples found")
    
    # Determine which indices to use
    if exclude_training_indices is not None and len(exclude_training_indices) > 0:
        # Exclude the specified indices
        available_indices = [i for i in range(total_examples) if i not in exclude_training_indices]
        
        # If excluding would leave too few examples, use all examples instead (fallback)
        min_examples = 3
        if len(available_indices) < min_examples:
            # Fallback: use all examples (different from excluding all)
            used_indices = list(range(total_examples))
            exclude_indices = None  # Don't exclude any
        else:
            used_indices = available_indices
            exclude_indices = exclude_training_indices
    else:
        # First generation: use all examples
        used_indices = list(range(total_examples))
        exclude_indices = None
    
    # Use the unified training system prompt with selected examples
    training_system_prompt = build_training_system_prompt(exclude_indices=exclude_indices)
    
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
        # Update the instructions to continue numbering - match exact text
        generation_instructions = GENERATION_INSTRUCTIONS.replace(
            "Number your FAQs starting from 1 (they will be appended to any existing FAQs).",
            f"Number your FAQs starting from {existing_faq_count + 1} (there are already {existing_faq_count} existing FAQs)."
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
        "max_completion_tokens": 1024  # Increased to handle longer responses
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        generated_prompt = result["choices"][0]["message"]["content"].strip()
        return generated_prompt, used_indices
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


def generate_faqs_with_rag(
    faqs: List[Dict[str, str]],
    scenario_prompt: str,
    retrieved_examples: List[Dict],
    existing_prompt: Optional[str] = None
) -> str:
    """
    Generate FAQs using RAG architecture with structured outputs.
    
    Args:
        faqs: List of FAQ dictionaries with 'trigger' and 'instruction' keys
        scenario_prompt: Scenario-specific system prompt
        retrieved_examples: List of retrieved FAQ examples from RAG
        existing_prompt: Optional existing system prompt to extract flows and FAQ context from
    
    Returns:
        Generated FAQ prompt text (converted from structured JSON)
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is required")
    
    if not faqs:
        raise ValueError("At least one FAQ is required")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Extract context from existing prompt if provided
    from utils.prompt_parser import extract_flows, extract_existing_faq_section, count_existing_faqs
    
    available_flows = []
    existing_faqs = ""
    existing_faq_count = 0
    
    if existing_prompt:
        available_flows = extract_flows(existing_prompt)
        existing_faqs = extract_existing_faq_section(existing_prompt)
        existing_faq_count = count_existing_faqs(existing_prompt)
    
    # Format available flows
    if available_flows:
        flows_text = "\n".join([f"- {flow}" for flow in available_flows])
    else:
        flows_text = "No specific flows found. Use phrases like 'return to the current step' or 'end the call' as appropriate."
    
    # Format existing FAQs
    if existing_faqs:
        existing_faqs_text = existing_faqs[:2000]
        if len(existing_faqs) > 2000:
            existing_faqs_text += "\n\n[... existing FAQs continue ...]"
    else:
        existing_faqs_text = "No existing FAQ section found. This will be the first FAQ section."
    
    # Format retrieved examples
    examples_text = ""
    if retrieved_examples:
        examples_text = "\n\n## RELEVANT EXAMPLES:\n\n"
        for i, example in enumerate(retrieved_examples[:5], 1):
            examples_text += f"Example {i}:\n"
            examples_text += f"Question: {example.get('question', '')}\n"
            examples_text += f"Answer: {example.get('answer', '')}\n"
            examples_text += f"Generated Prompt:\n{example.get('generated_prompt', '')}\n\n"
    
    # Build user prompt
    faqs_text = "\n".join([
        f"{i+1}. Question: \"{faq['trigger']}\"\n   Answer: {faq['instruction']}"
        for i, faq in enumerate(faqs)
    ])
    
    numbering_note = ""
    start_num = existing_faq_count + 1 if existing_faq_count > 0 else 1
    if existing_faq_count > 0:
        numbering_note = f"\n\nIMPORTANT: Continue numbering from {start_num}. The last existing FAQ is numbered {existing_faq_count}."
    
    user_prompt = f"""Convert the following FAQs into system prompt sections.

AVAILABLE FLOWS:
{flows_text}

EXISTING FAQ CONTEXT:
{existing_faqs_text}
{numbering_note}

{examples_text}

FAQs TO CONVERT:
{faqs_text}

Generate prompt sections that:
- Match the style and structure of the examples above
- Use only flows listed in AVAILABLE FLOWS
- Continue numbering from existing FAQs if any exist (start from {start_num})
- Each FAQ section must start with a numbered item (e.g., "{start_num}. If the user...")
- Match complexity to each FAQ (simple FAQs stay simple, complex ones can be nested)

CRITICAL NUMBERING REQUIREMENT: 
- If there are existing FAQs shown above, you MUST start numbering from {start_num}
- The first FAQ you generate must be numbered {start_num}, the second {start_num + 1 if len(faqs) > 1 else start_num}, etc.
- DO NOT start from 1 if there are existing FAQs - always continue from {start_num}
- Each generated_prompt field in the JSON response must start with the correct number: {start_num}, {start_num + 1 if len(faqs) > 1 else start_num}, etc."""

    # JSON Schema for structured output
    json_schema = {
        "type": "object",
        "properties": {
            "faqs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                        "generated_prompt": {"type": "string"},
                        "scenario_tags": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["question", "answer", "generated_prompt"]
                }
            }
        },
        "required": ["faqs"]
    }
    
    try:
        # Try structured outputs first (for models that support it)
        try:
            response = client.chat.completions.create(
                model=GENERATION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": scenario_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "faq_generation",
                        "schema": json_schema
                    }
                },
                temperature=0.1,
                max_completion_tokens=2000
            )
        except Exception as structured_error:
            # Fallback: Use json_object mode if json_schema is not supported
            error_str = str(structured_error)
            if "json_schema" in error_str.lower() or "response_format" in error_str.lower():
                # Try with json_object mode instead
                response = client.chat.completions.create(
                    model=GENERATION_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": scenario_prompt + "\n\nIMPORTANT: You must respond with valid JSON only, following this exact structure: {\"faqs\": [{\"question\": \"...\", \"answer\": \"...\", \"generated_prompt\": \"...\", \"scenario_tags\": [...], \"confidence\": 0.9}]}"
                        },
                        {
                            "role": "user",
                            "content": user_prompt + "\n\nRemember: Respond with valid JSON only, no markdown, no code blocks."
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_completion_tokens=2000
                )
            else:
                # Re-raise if it's a different error
                raise
        
        # Parse structured output
        result_json = json.loads(response.choices[0].message.content)
        faqs_data = result_json.get("faqs", [])
        
        # Convert to prompt text format with proper numbering
        import re
        prompt_parts = []
        start_number = existing_faq_count + 1 if existing_faq_count > 0 else 1
        
        for i, faq_data in enumerate(faqs_data):
            generated_prompt = faq_data.get("generated_prompt", "")
            
            # Ensure numbering is correct - replace any existing numbers with correct ones
            if generated_prompt:
                # Calculate the correct number for this FAQ
                correct_number = start_number + i
                
                # Strip leading whitespace first
                generated_prompt = generated_prompt.strip()
                
                # Match patterns like "1.", "1. ", "1) ", etc. at the start of the line
                # Also handle cases where there might be whitespace before the number
                numbered_pattern = r'^\d+[\.\)]\s+'
                
                # Check if it starts with a number
                if re.match(numbered_pattern, generated_prompt):
                    # Replace the number at the start with the correct number
                    generated_prompt = re.sub(
                        numbered_pattern,
                        f"{correct_number}. ",
                        generated_prompt,
                        count=1
                    )
                else:
                    # If no number at the start, add one
                    generated_prompt = f"{correct_number}. {generated_prompt}"
                
                prompt_parts.append(generated_prompt)
        
        return "\n\n".join(prompt_parts)
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse structured output: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to generate FAQ prompt: {str(e)}")


