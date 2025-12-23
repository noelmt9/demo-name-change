"""Prompt training configuration for OpenAI FAQ generation.

This file contains your writing style examples and training instructions.
The model will learn from these examples to generate prompts in your style.
"""

from pathlib import Path
from typing import Optional
import hashlib
import os

# Get the prompts directory paths (relative to this file)
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_TRAINING_EXAMPLES_DIR = _PROMPTS_DIR / "training_examples"
_SYSTEM_PROMPTS_DIR = _PROMPTS_DIR / "system_prompts"


def load_writing_style_examples() -> list[str]:
    """
    Load writing style examples from the training_examples directory.
    
    These show the conversion pattern: how to convert FAQ triggers/instructions
    into well-formatted prompt sections.
    
    Each .txt file in the training_examples/ directory represents a different example.
    Files are loaded in alphabetical order.
    
    Returns:
        List of example strings loaded from prompt files
    """
    examples = []
    
    if not _TRAINING_EXAMPLES_DIR.exists():
        # If training examples directory doesn't exist, return empty list
        return examples
    
    # Get all .txt files in the training examples directory, sorted alphabetically
    example_files = sorted(_TRAINING_EXAMPLES_DIR.glob("*.txt"))
    
    for example_file in example_files:
        try:
            with open(example_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:  # Only add non-empty files
                    examples.append(content)
        except Exception as e:
            # Log error but continue loading other files
            print(f"Warning: Could not load training example file {example_file}: {e}")
    
    return examples


def load_all_system_prompts_as_examples() -> list[str]:
    """
    Load a REPRESENTATIVE SAMPLE of system prompts (3-5 diverse ones) instead of all prompts.
    
    This is much more efficient than loading all 17 prompts (~750k chars). By sampling
    diverse prompts (B2B, 3P, 1P, Inbound, Outbound), the model learns the writing style
    without the overhead of sending everything every time.
    
    Returns:
        List of system prompt strings (sample of diverse prompts)
    """
    examples = []
    
    if not _SYSTEM_PROMPTS_DIR.exists():
        return examples
    
    # Get all .txt files in the system prompts directory, sorted alphabetically
    prompt_files = sorted(_SYSTEM_PROMPTS_DIR.glob("*.txt"))
    
    if not prompt_files:
        return examples
    
    # Strategy: Sample diverse prompts to represent different styles
    # We want max 3-5 prompts that cover different categories
    MAX_SAMPLE_SIZE = 4
    
    # Priority categories to ensure diversity
    categories = {
        'b2b': None,
        '3p': None,
        '1p': None,
        'inbound': None,
        'outbound': None
    }
    
    # First pass: Try to get one from each category
    for prompt_file in prompt_files:
        filename_lower = prompt_file.stem.lower()
        
        # Check categories (prioritize Generic over CarMax for diversity)
        if 'b2b' in filename_lower and categories['b2b'] is None:
            if 'generic' in filename_lower:  # Prefer Generic over CarMax
                categories['b2b'] = prompt_file
            elif categories['b2b'] is None:
                categories['b2b'] = prompt_file
        elif '3p' in filename_lower and 'generic' in filename_lower and categories['3p'] is None:
            categories['3p'] = prompt_file
        elif '1p' in filename_lower and 'generic' in filename_lower and categories['1p'] is None:
            categories['1p'] = prompt_file
        elif ('ib' in filename_lower or 'inbound' in filename_lower) and categories['inbound'] is None:
            if 'generic' in filename_lower:
                categories['inbound'] = prompt_file
        elif ('ob' in filename_lower or 'outbound' in filename_lower) and categories['outbound'] is None:
            if 'generic' in filename_lower:
                categories['outbound'] = prompt_file
    
    # Collect selected files from categories
    selected_files = []
    for category_file in categories.values():
        if category_file is not None and len(selected_files) < MAX_SAMPLE_SIZE:
            selected_files.append(category_file)
    
    # If we don't have enough diverse samples, fill with remaining files
    for prompt_file in prompt_files:
        if prompt_file not in selected_files and len(selected_files) < MAX_SAMPLE_SIZE:
            selected_files.append(prompt_file)
    
    # Load the selected prompts
    for prompt_file in selected_files:
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    examples.append(f"=== Example Style from {prompt_file.stem} ===\n{content}")
        except Exception as e:
            print(f"Warning: Could not load system prompt file {prompt_file}: {e}")
    
    return examples


# Cache for training system prompt
_training_prompt_cache = None
_training_prompt_cache_hash = None


def _get_prompts_hash() -> str:
    """
    Generate a hash of all prompt files' modification times to detect changes.
    This allows us to invalidate the cache when prompts are updated.
    """
    hasher = hashlib.md5()
    
    # Hash system prompts directory
    if _SYSTEM_PROMPTS_DIR.exists():
        for prompt_file in sorted(_SYSTEM_PROMPTS_DIR.glob("*.txt")):
            try:
                mtime = os.path.getmtime(prompt_file)
                hasher.update(f"{prompt_file.name}:{mtime}".encode())
            except:
                pass
    
    # Hash training examples directory
    if _TRAINING_EXAMPLES_DIR.exists():
        for example_file in sorted(_TRAINING_EXAMPLES_DIR.glob("*.txt")):
            try:
                mtime = os.path.getmtime(example_file)
                hasher.update(f"{example_file.name}:{mtime}".encode())
            except:
                pass
    
    return hasher.hexdigest()


def build_training_system_prompt() -> str:
    """
    Build a unified training system prompt using a smart sample of system prompts.
    
    This function:
    1. Loads a diverse sample of system prompts (3-5) as style examples
    2. Loads all training examples (conversion patterns)
    3. Combines them into a master training prompt
    4. Caches the result and only rebuilds when prompts change
    
    Returns:
        Complete system prompt string for training OpenAI
    """
    global _training_prompt_cache, _training_prompt_cache_hash
    
    # Check if cache is valid
    current_hash = _get_prompts_hash()
    if _training_prompt_cache is not None and _training_prompt_cache_hash == current_hash:
        return _training_prompt_cache
    
    # Cache miss or invalid - rebuild
    # Load conversion pattern examples (FAQ → prompt format)
    conversion_examples = load_writing_style_examples()
    
    # Load a smart sample of system prompts (not all of them)
    style_examples = load_all_system_prompts_as_examples()
    
    # Build the training prompt
    training_prompt = """You are a prompt engineer specializing in debt collection voicebot systems. Your task is to convert FAQ information into system prompt sections that match a specific writing style.

## STYLE REFERENCE

Study these examples carefully. They demonstrate the exact writing patterns you must replicate:

{conversion_examples}

## STYLE PATTERNS TO MATCH

Based on the examples above, follow these patterns:

**Opening Structure**
- Start with "If the user..." to define the trigger condition
- Combine related triggers with "or" (e.g., "mentions selling their vehicle or asks about selling the car")

**Acknowledgment Pattern**
- Always acknowledge the user's statement before taking action
- Use phrases like "acknowledge their concern", "acknowledge their request", "acknowledge their situation with empathy"
- Never skip acknowledgment, even for simple requests

**Natural Language Flow**
- Use "let them know" instead of "inform them" or "tell them"
- Use "ask if they'd like to" instead of "inquire whether they would prefer"
- Use "that's something an agent can walk them through" instead of "an agent can assist with that matter"

**Conditional Branching**
- Use "If the user agrees..." and "If the user declines..." for binary outcomes
- Use "Based on their response" when routing depends on user input
- Keep conditions at the same indentation level when they're alternatives

**Flow Transitions**
- End with clear flow references: "Move to the TRANSFER FLOW", "Move to the MAKE PAYMENT FLOW"
- Use "immediately end the call" for terminal states
- Never leave the next step ambiguous

**Tone**
- Professional but conversational
- Empathetic without being overly soft
- Direct without being aggressive

## ADDITIONAL STYLE CONTEXT

{style_examples}

## OUTPUT REQUIREMENTS

When converting FAQs:

1. Match the voice and phrasing of the examples exactly
2. Embed the bot response instruction into natural conditional logic
3. Include appropriate acknowledgment before every action
4. Specify the exact flow to transition to when applicable
5. Write as continuous prose, not bullet points or numbered steps
6. Keep each prompt section focused on a single user intent"""
    
    # Format the prompt with actual examples
    conversion_text = "\n\n".join(conversion_examples) if conversion_examples else "No conversion examples provided."
    style_text = "\n\n".join(style_examples) if style_examples else "No style examples provided."
    
    result = training_prompt.format(
        conversion_examples=conversion_text,
        style_examples=style_text
    )
    
    # Update cache
    _training_prompt_cache = result
    _training_prompt_cache_hash = current_hash
    
    return result


def load_system_prompt(prompt_name: str = "default") -> str:
    """
    DEPRECATED: This function is kept for backward compatibility but now always uses
    the unified training approach with all system prompts.
    
    Use build_training_system_prompt() instead.
    """
    return build_training_system_prompt()


def list_available_system_prompts() -> list[str]:
    """
    List all available system prompt names (without .txt extension).
    
    Returns:
        List of system prompt names available in the system_prompts directory.
    """
    if not _SYSTEM_PROMPTS_DIR.exists():
        return []
    
    prompt_files = sorted(_SYSTEM_PROMPTS_DIR.glob("*.txt"))
    return [f.stem for f in prompt_files]


# Load writing style examples from the training_examples directory
WRITING_STYLE_EXAMPLES = load_writing_style_examples()


# Generation instructions for converting FAQs
GENERATION_INSTRUCTIONS = """
Convert the following FAQs into system prompt sections.

TASK:
For each FAQ, generate a prompt section that:
- Starts with "If the user..." defining the trigger
- Acknowledges the user's intent before acting
- Provides specific instructions in natural prose
- Ends with a clear flow transition when applicable

STYLE ENFORCEMENT:
- Write as if you authored the examples in the STYLE REFERENCE section
- Use identical phrasing patterns: "acknowledge their...", "let them know...", "ask if they'd like to..."
- Match the level of detail shown in the examples
- Do not use bullet points, numbered lists, or headers within the prompt section

FAQs:
{faqs}

Generate one prompt section per FAQ. Each section should integrate seamlessly with an existing voicebot system prompt.
"""