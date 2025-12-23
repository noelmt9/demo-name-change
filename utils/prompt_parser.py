
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


def append_faq_prompt(prompt: str, faq_prompt: str) -> str:
    """
    Append the FAQ prompt to the main system prompt.
    
    Args:
        prompt: The main system prompt
        faq_prompt: The FAQ prompt to append
        
    Returns:
        Combined prompt with FAQ section appended
    """
    if not faq_prompt:
        return prompt
    
    # Append with proper spacing
    if prompt.endswith('\n'):
        return prompt + faq_prompt
    else:
        return prompt + '\n\n' + faq_prompt