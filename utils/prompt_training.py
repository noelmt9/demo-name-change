"""Prompt training configuration for OpenAI FAQ generation.

This file contains your writing style examples and training instructions.
The model will learn from these examples to generate prompts in your style.
"""

from pathlib import Path
import hashlib
import os

# Get the prompts directory paths (relative to this file)
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_TRAINING_EXAMPLES_DIR = _PROMPTS_DIR / "training_examples"


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


# Cache for training system prompt
_training_prompt_cache = None
_training_prompt_cache_hash = None


def _get_prompts_hash() -> str:
    """
    Generate a hash of all training example files' modification times to detect changes.
    This allows us to invalidate the cache when training examples are updated.
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
    
    return hasher.hexdigest()


def build_training_system_prompt() -> str:
    """
    Build a unified training system prompt using only training examples.
    
    This function:
    1. Loads all training examples (nested structure examples)
    2. Combines them into a master training prompt
    3. Caches the result and only rebuilds when training examples change
    
    Returns:
        Complete system prompt string for training OpenAI
    """
    global _training_prompt_cache, _training_prompt_cache_hash
    
    # Check if cache is valid
    current_hash = _get_prompts_hash()
    if _training_prompt_cache is not None and _training_prompt_cache_hash == current_hash:
        return _training_prompt_cache
    
    # Cache miss or invalid - rebuild
    # Load training examples (nested structure examples)
    conversion_examples = load_writing_style_examples()
    
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
    
    # Update cache
    _training_prompt_cache = result
    _training_prompt_cache_hash = current_hash
    
    return result


# Load writing style examples from the training_examples directory
WRITING_STYLE_EXAMPLES = load_writing_style_examples()


# Generation instructions for converting FAQs
GENERATION_INSTRUCTIONS = """
Convert the following FAQs into system prompt sections with nested conditional structure.

CRITICAL STRUCTURE REQUIREMENTS:
1. Use numbered format (1., 2., etc.) for main triggers
2. Use indented dashes (-) for nested conditions that handle follow-up responses
3. Use double/triple indentation for deeper nesting when needed
4. Each nested level must specify what happens next (flow transition, return to step, etc.)

AVAILABLE FLOWS:
The following flows are available in the existing system prompt. ONLY reference these flows - do not create new flow names:
{available_flows}

If no flows are listed above, you may use common flows like "TRANSFER FLOW" or "MAKE PAYMENT FLOW" if they make sense contextually, but prefer returning to the current step or ending the call when flows are not available.

EXISTING FAQ CONTEXT:
Below is the existing FAQ section from the prompt (if any). Your new FAQs will be appended to this section. Ensure your generated FAQs are consistent in style and structure:
{existing_faqs}

TASK:
For each FAQ, generate a prompt section that:
- Starts with a numbered item (1., 2., etc.) and "If the user..." defining the trigger
- Includes nested indented conditions (-) to handle objections, follow-up questions, and different user responses
- At each nested level, provides context on what to do next (flow transition, return to current step, etc.)
- Acknowledges the user's intent before acting at every level
- Ends nested branches with clear flow transitions when applicable
- ONLY references flows that are listed in AVAILABLE FLOWS above
- Keeps each FAQ section concise (aim for 200-400 words per FAQ, not overly verbose)

LENGTH CONSTRAINT:
Keep each FAQ section reasonably concise. Avoid excessive nesting beyond 3-4 levels unless absolutely necessary. The goal is clarity and actionability, not exhaustive coverage of every possible scenario.

STYLE ENFORCEMENT:
- Write as if you authored the examples in the STYLE REFERENCE section
- Use identical phrasing patterns: "acknowledge their...", "let them know...", "pivot to a constructive solution..."
- Match the nested structure shown in the examples (numbered items with indented dashes)
- Include context about returning to flows: "return to the current step", "seamlessly return to the last point"
- Match the level of detail and nested logic shown in the examples

FAQs TO CONVERT:
{faqs}

Generate one prompt section per FAQ. Each section should use nested conditional structure and integrate seamlessly with the existing voicebot system prompt. Number your FAQs starting from 1 (they will be appended to any existing FAQs).
"""