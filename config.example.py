"""Configuration constants for the application.

Copy this file to config.py and fill in your API keys.
Never commit config.py to version control.
"""

import os

# API Configuration
VAPI_API_BASE_URL = "https://api.vapi.ai"
OPENAI_API_BASE_URL = "https://api.openai.com/v1"

# API Keys - Set these in environment variables or update directly here
# For production, use environment variables: os.getenv("VAPI_API_KEY", "your-key-here")
# The first parameter is the environment variable name, second is the default value
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "your-vapi-api-key-here")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

# Session State Keys
ASSISTANTS_STORAGE_KEY = "assistants"
SELECTED_ASSISTANT_STORAGE_KEY = "selected_assistant"
VARIABLES_STORAGE_KEY = "variables"
FAQS_STORAGE_KEY = "faqs"
SYSTEM_PROMPT_STORAGE_KEY = "system_prompt"
FAQ_PROMPT_STORAGE_KEY = "faq_prompt"  # Generated FAQ prompt from OpenAI

