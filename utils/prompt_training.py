"""Prompt training configuration for OpenAI FAQ generation.

This file contains your writing style examples and training instructions.
The model will learn from these examples to generate prompts in your style.
"""

from pathlib import Path
import hashlib
import os
from typing import Optional, List

# Get the prompts directory paths (relative to this file)
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_TRAINING_EXAMPLES_DIR = _PROMPTS_DIR / "training_examples"


def load_writing_style_examples(exclude_indices: Optional[List[int]] = None) -> list[str]:
    """
    Load writing style examples from the training_examples directory.
    
    These show the conversion pattern: how to convert FAQ triggers/instructions
    into well-formatted prompt sections.
    
    Each .txt file in the training_examples/ directory represents a different example.
    Files are loaded in alphabetical order.
    
    Args:
        exclude_indices: Optional list of indices to exclude (0-based). If provided,
                        these example indices will be skipped. If excluding would leave
                        fewer than 3 examples, all examples are used instead.
    
    Returns:
        List of example strings loaded from prompt files
    """
    examples = []
    
    if not _TRAINING_EXAMPLES_DIR.exists():
        # If training examples directory doesn't exist, return empty list
        return examples
    
    # Get all .txt files in the training examples directory, sorted alphabetically
    example_files = sorted(_TRAINING_EXAMPLES_DIR.glob("*.txt"))
    
    # Load all examples first
    all_examples = []
    for example_file in example_files:
        try:
            with open(example_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:  # Only add non-empty files
                    all_examples.append(content)
        except Exception as e:
            # Log error but continue loading other files
            print(f"Warning: Could not load training example file {example_file}: {e}")
    
    # If no exclusion requested, return all examples
    if exclude_indices is None or len(exclude_indices) == 0:
        return all_examples
    
    # Filter out excluded indices
    filtered_examples = [
        example for idx, example in enumerate(all_examples)
        if idx not in exclude_indices
    ]
    
    # Ensure we have at least 3 examples (fallback to all if too many excluded)
    min_examples = 3
    if len(filtered_examples) < min_examples and len(all_examples) >= min_examples:
        # Too many excluded, use all examples instead
        return all_examples
    
    return filtered_examples


# Cache for training system prompt (separate caches for different exclusion sets)
_training_prompt_cache = {}
_training_prompt_cache_hash = {}


def _get_prompts_hash(exclude_indices: Optional[List[int]] = None) -> str:
    """
    Generate a hash of all training example files' modification times to detect changes.
    This allows us to invalidate the cache when training examples are updated.
    Also includes exclusion indices in the hash to cache different exclusion sets separately.
    """
    hasher = hashlib.md5()
    
    # Hash training examples directory (only source we use now)
    if _TRAINING_EXAMPLES_DIR.exists():
        for example_file in sorted(_TRAINING_EXAMPLES_DIR.glob("*.txt")):
            try:
                mtime = os.path.getmtime(example_file)
                hasher.update(f"{example_file.name}:{mtime}".encode())
            except:
                pass
    
    # Include exclusion indices in hash to cache different exclusion sets separately
    if exclude_indices:
        exclude_str = ",".join(sorted(str(idx) for idx in exclude_indices))
        hasher.update(f"exclude:{exclude_str}".encode())
    else:
        hasher.update("exclude:none".encode())
    
    return hasher.hexdigest()


def build_training_system_prompt(exclude_indices: Optional[List[int]] = None) -> str:
    """
    Build a unified training system prompt using only training examples.
    
    This function:
    1. Loads training examples (nested structure examples), optionally excluding some
    2. Combines them into a master training prompt
    3. Caches the result and only rebuilds when training examples change or exclusion changes
    
    Args:
        exclude_indices: Optional list of example indices to exclude from training
    
    Returns:
        Complete system prompt string for training OpenAI
    """
    global _training_prompt_cache, _training_prompt_cache_hash
    
    # Create cache key from exclusion indices
    cache_key = tuple(sorted(exclude_indices)) if exclude_indices else None
    
    # Check if cache is valid
    current_hash = _get_prompts_hash(exclude_indices)
    if cache_key in _training_prompt_cache and cache_key in _training_prompt_cache_hash:
        if _training_prompt_cache_hash[cache_key] == current_hash:
            return _training_prompt_cache[cache_key]
    
    # Cache miss or invalid - rebuild
    # Load training examples (nested structure examples) with exclusion
    conversion_examples = load_writing_style_examples(exclude_indices)
    
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

**Nested Conditional Structure (CRITICAL)**
- Use numbered items (1., 2., etc.) for main triggers
- Use indented dashes (-) for first-level nested conditions
- Use double-indented dashes (    -) for second-level nested conditions
- Use triple-indented dashes (        -) for third-level nested conditions
- Each nested level should handle a specific user response or objection
- Always provide context on what to do next after each response

**Conditional Branching**
- Use "If the user agrees..." and "If the user declines..." for binary outcomes
- Use "Based on their response" when routing depends on user input
- Keep conditions at the same indentation level when they're alternatives
- Structure nested conditionals to handle objections and follow-up questions

**Flow Transitions**
- End nested branches with clear flow references: "go to the MAKE PAYMENT FLOW", "transfer the call using the TRANSFER FLOW"
- Use "immediately end the call" for terminal states
- Never leave the next step ambiguous
- Always specify the flow transition at the appropriate nested level

**Tone**
- Professional but conversational
- Empathetic without being overly soft
- Direct without being aggressive

## STYLE NOTES

The examples above demonstrate the complete writing style, structure, and patterns you must replicate. Study them carefully to understand:
- The exact nested conditional structure (numbered items with indented dashes)
- How to handle objections and follow-up questions at nested levels
- How to provide context about flow transitions and returning to steps
- The specific phrasing and tone used throughout

These examples contain all the style information you need - no additional context is required.

## OUTPUT REQUIREMENTS

When converting FAQs:

1. **Structure**: Use numbered items (1., 2.) for main triggers, with nested indented dashes (-) for follow-up conditions
2. **Nested Logic**: Create nested conditionals to handle objections, follow-up questions, and different user responses
3. **Flow Context**: At each nested level, specify what should happen next (flow transition, return to current step, etc.)
4. **Acknowledgment**: Include appropriate acknowledgment before every action, even in nested branches
5. **Voice Match**: Match the voice and phrasing of the examples exactly
6. **Flow Transitions**: Always end with clear flow references at the appropriate nested level
7. **Context Preservation**: When returning to a flow, specify "return to the current step" or "seamlessly return to the last point" to maintain context"""
    
    # Format the prompt with actual examples
    conversion_text = "\n\n".join(conversion_examples) if conversion_examples else "No conversion examples provided."
    
    result = training_prompt.format(
        conversion_examples=conversion_text
    )
    
    # Update cache for this exclusion set
    _training_prompt_cache[cache_key] = result
    _training_prompt_cache_hash[cache_key] = current_hash
    
    return result


# Load writing style examples from the training_examples directory
WRITING_STYLE_EXAMPLES = load_writing_style_examples()


# Generation instructions for converting FAQs
GENERATION_INSTRUCTIONS = """
Convert the following FAQs into system prompt sections that match the complexity of each FAQ.

CRITICAL STRUCTURE REQUIREMENTS:
1. Use numbered format (1., 2., etc.) for main triggers
2. **Match complexity to the FAQ**: Simple questions get simple responses, complex scenarios can use nested conditions
3. Use indented dashes (-) for nested conditions ONLY when the FAQ requires handling multiple follow-up scenarios
4. Each nested level (if used) must specify what happens next (flow transition, return to step, etc.)

AVAILABLE FLOWS:
The following flows are available in the existing system prompt. **YOU MUST ONLY reference these flows** - do not create new flow names:
{available_flows}

**CRITICAL FLOW RESTRICTION**: 
- If flows are listed above, you MUST use only those flows. Never reference a flow that is not in the list above.
- If no flows are listed above, you MUST NOT create or reference any flows. Instead, use phrases like "return to the current step" or "seamlessly return to the last point" or "end the call" as appropriate.
- Never invent flow names like "PAYMENT PLAN FLOW" if it's not in the AVAILABLE FLOWS list.

EXISTING FAQ CONTEXT:
Below is the existing FAQ section from the prompt (if any). Your new FAQs will be appended to this section. Ensure your generated FAQs are consistent in style and structure:
{existing_faqs}

TASK:
For each FAQ, generate a prompt section that:
- Starts with a numbered item (1., 2., etc.) and "If the user..." defining the trigger
- **Matches the complexity**: If the FAQ is simple (e.g., "transfer to agent"), keep it simple. If it requires handling objections or multiple scenarios, use nested conditions.
- May include nested indented conditions (-) ONLY when needed to handle objections, follow-up questions, or different user responses
- At each nested level (if used), provides context on what to do next (flow transition, return to current step, etc.)
- Acknowledges the user's intent before acting
- Ends with clear flow transitions when applicable (using ONLY flows from AVAILABLE FLOWS)
- Keeps each FAQ section appropriately sized - simple FAQs should be brief, complex ones can be longer

LENGTH CONSTRAINT:
Keep each FAQ section reasonably concise. Avoid excessive nesting beyond 3-4 levels unless absolutely necessary. The goal is clarity and actionability, not exhaustive coverage of every possible scenario.

STYLE ENFORCEMENT:
- Write as if you authored the examples in the STYLE REFERENCE section
- Use identical phrasing patterns: "acknowledge their...", "let them know...", "pivot to a constructive solution..."
- Match the structure shown in the examples when complexity is similar (numbered items with indented dashes for complex scenarios)
- Include context about returning to flows: "return to the current step", "seamlessly return to the last point"
- Match the level of detail appropriate for each FAQ - simple FAQs don't need the same detail as complex ones

**FAQ SECTION CREATION**:
- If existing FAQs are shown above, your new FAQs will be appended to that section - do not create a new heading.
- If no existing FAQs are shown, you may need to create a new FAQ section, but the system will handle the heading automatically - just generate the FAQ content.

FAQs TO CONVERT:
{faqs}

Generate one prompt section per FAQ. Each section should integrate seamlessly with the existing voicebot system prompt.

**NUMBERING REQUIREMENT**: 
- If there are existing FAQs in the prompt above, you MUST continue the numbering from where they left off. For example, if the last existing FAQ is numbered "3.", your first new FAQ must be numbered "4.", not "1.".
- If no existing FAQs exist, start from "1."
- The numbering is critical - do not restart numbering.
"""