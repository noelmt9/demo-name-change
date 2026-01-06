
"""Prompt parsing and manipulation utilities."""

import re
from typing import List, Dict


def extract_variables(prompt: str) -> List[str]:
    """
    Extract all variables from a system prompt in the format {{variableName}}.
    
    Args:
        prompt: The system prompt string
        
    Returns:
        List of unique variable names (without the {{}} brackets)
    """
    variable_pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(variable_pattern, prompt)
    # Return unique variable names in order of first appearance
    seen = set()
    result = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            result.append(match)
    return result


def replace_variables(prompt: str, variables: Dict[str, str]) -> str:
    """
    Replace variables in the prompt with their values.
    Only replaces variables that have non-empty values.
    
    Args:
        prompt: The system prompt string
        variables: Dictionary mapping variable names to their values
        
    Returns:
        Updated prompt with variables replaced
    """
    result = prompt
    for var_name, var_value in variables.items():
        if var_value:  # Only replace if value is not empty
            pattern = r'\{\{' + re.escape(var_name) + r'\}\}'
            result = re.sub(pattern, var_value, result)
    return result


def extract_flows(prompt: str) -> List[str]:
    """
    Extract all flow names from a system prompt.
    Looks for patterns like "MAKE PAYMENT FLOW", "TRANSFER FLOW", etc.
    
    Args:
        prompt: The system prompt string
        
    Returns:
        List of unique flow names (e.g., ["MAKE PAYMENT FLOW", "TRANSFER FLOW"])
    """
    # Pattern to match flow names: "go to the X FLOW", "move to the X FLOW", "X FLOW", etc.
    # Matches patterns like: "MAKE PAYMENT FLOW", "TRANSFER FLOW", "FULL PAYMENT FLOW"
    flow_pattern = r'\b([A-Z][A-Z\s]+FLOW)\b'
    matches = re.findall(flow_pattern, prompt)
    
    # Clean up and deduplicate
    seen = set()
    result = []
    for match in matches:
        # Clean up extra spaces
        cleaned = ' '.join(match.split())
        if cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    
    return result


def extract_existing_faq_section(prompt: str) -> str:
    """
    Extract existing FAQ section from the prompt if it exists.
    Looks for sections under headings like "## FAQ", "### FAQ", "## FAQs", "## FAQs:", 
    "### FAQ Workflows", etc.
    
    Args:
        prompt: The system prompt string
        
    Returns:
        Existing FAQ section text, or empty string if not found
    """
    # Pattern to match FAQ headings found in system prompts:
    # - "## FAQ" or "### FAQ"
    # - "## FAQs" or "## FAQs:" (with optional colon)
    # - "### FAQ Workflows"
    # Matches: ## or ###, space, FAQ or FAQs, optional " Workflows", optional colon/space
    faq_heading_pattern = r'^#{2,3}\s+FAQs?(?:\s+Workflows?)?[:\s]*$'
    
    # Find all FAQ headings
    lines = prompt.split('\n')
    faq_sections = []
    current_faq_start = None
    
    for i, line in enumerate(lines):
        # Check if this line is an FAQ heading
        if re.match(faq_heading_pattern, line, re.IGNORECASE):
            current_faq_start = i
        elif current_faq_start is not None:
            # Check if we've hit another major heading (## or ###) that's not an FAQ heading
            if re.match(r'^#{2,3}\s+[^#]', line):
                # Check if this new heading is also an FAQ heading (in case there are multiple FAQ sections)
                if not re.match(faq_heading_pattern, line, re.IGNORECASE):
                    # This is a different section heading, extract everything up to here
                    faq_section = '\n'.join(lines[current_faq_start:i])
                    if faq_section.strip():
                        faq_sections.append(faq_section.strip())
                    current_faq_start = None
                else:
                    # This is another FAQ heading, save previous section and start new one
                    faq_section = '\n'.join(lines[current_faq_start:i])
                    if faq_section.strip():
                        faq_sections.append(faq_section.strip())
                    current_faq_start = i
    
    # If we found an FAQ section and didn't hit another heading, extract to end of document
    if current_faq_start is not None:
        faq_section = '\n'.join(lines[current_faq_start:])
        if faq_section.strip():
            faq_sections.append(faq_section.strip())
    
    if faq_sections:
        # Return all FAQ sections found, joined with double newlines
        return '\n\n'.join(faq_sections)
    
    return ""


def count_existing_faqs(prompt: str) -> int:
    """
    Find the highest numbered FAQ in the prompt to determine where to continue numbering.
    FAQ items are identified by any numbered items (e.g., "1. ", "2. ", etc.)
    within the FAQ section.
    
    Args:
        prompt: The system prompt string
    
    Returns:
        Highest FAQ number found (0 if none found)
    """
    # First extract the FAQ section
    faq_section = extract_existing_faq_section(prompt)
    
    if not faq_section:
        return 0
    
    # Find all numbered items in the FAQ section
    # Pattern matches: "1. ", "2. ", "10. ", etc. at the start of a line
    # This matches any numbered FAQ, not just ones starting with "If the user"
    faq_count_pattern = r'^(\d+)\.\s+'
    matches = re.findall(faq_count_pattern, faq_section, re.MULTILINE)
    
    if not matches:
        return 0
    
    # Extract the numbers and return the maximum (highest FAQ number)
    numbers = [int(match) for match in matches]
    return max(numbers)


def append_faq_prompt(prompt: str, faq_prompt: str) -> str:
    """
    Insert the FAQ prompt into the existing FAQ section (at the end of the FAQ content),
    or append at the end if no FAQ section exists.
    
    Args:
        prompt: The main system prompt
        faq_prompt: The FAQ prompt to insert/append
        
    Returns:
        Combined prompt with FAQ content inserted into existing FAQ section
    """
    if not faq_prompt:
        return prompt
    
    # Pattern to match FAQ headings
    faq_heading_pattern = r'^#{2,3}\s+FAQs?(?:\s+Workflows?)?[:\s]*$'
    
    lines = prompt.split('\n')
    faq_start_index = None
    faq_end_index = None
    
    # Find the FAQ section boundaries
    for i, line in enumerate(lines):
        if re.match(faq_heading_pattern, line, re.IGNORECASE):
            faq_start_index = i
        elif faq_start_index is not None:
            # Check if we've hit another major heading (## or ###) that's not an FAQ heading
            if re.match(r'^#{2,3}\s+[^#]', line):
                if not re.match(faq_heading_pattern, line, re.IGNORECASE):
                    # This is a different section heading, FAQ section ends here
                    faq_end_index = i
                    break
    
    if faq_start_index is not None:
        # FAQ section exists - insert the new FAQ content at the end of the FAQ section
        # Split faq_prompt into lines for proper insertion
        faq_prompt_lines = faq_prompt.split('\n')
        
        if faq_end_index is not None:
            # Insert at the end of FAQ section, before the next section
            # Add the new FAQ content with proper spacing
            new_lines = (
                lines[:faq_end_index] + 
                [''] +  # Empty line for spacing
                faq_prompt_lines + 
                [''] +  # Empty line for spacing
                lines[faq_end_index:]
            )
        else:
            # FAQ section goes to end of document - append within FAQ section
            # Find the last non-empty line in the FAQ section
            last_faq_line = len(lines) - 1
            while last_faq_line > faq_start_index and not lines[last_faq_line].strip():
                last_faq_line -= 1
            
            # Insert after the last FAQ content, before end of document
            new_lines = (
                lines[:last_faq_line + 1] + 
                [''] +  # Empty line for spacing
                faq_prompt_lines
            )
        
        return '\n'.join(new_lines)
    else:
        # No FAQ section exists - append at the end with a new FAQ heading
        # Determine appropriate heading level (use ## if most sections use ##, ### if they use ###)
        has_three_hash = any(re.match(r'^###\s+', line) for line in lines)
        heading_level = '###' if has_three_hash else '##'
    
    # Append with proper spacing
    if prompt.endswith('\n'):
            return prompt + f'{heading_level} FAQs\n\n{faq_prompt}'
    else:
            return prompt + f'\n\n{heading_level} FAQs\n\n{faq_prompt}'