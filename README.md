# VAPI Assistant Manager

A Streamlit web dashboard for managing VAPI voice assistant configurations, including dynamic variables and OpenAI-powered FAQ prompt generation.

## Features

- **Variable Management**: Update dynamic variables in system prompts (e.g., `{{botName}}`, `{{companyName}}`) - all fields are optional
- **FAQ Management**: Add, edit, and delete custom FAQ entries
- **OpenAI Integration**: Convert FAQs into system prompts using OpenAI API with customizable prompt templates
- **Assistant Selection**: Browse and select from all your VAPI assistants
- **Modular Architecture**: Clean code structure with separate modules for services and utilities

## Project Structure

```
.
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration constants (not in git - copy from config.example.py)
├── config.example.py           # Configuration template
├── services/
│   ├── __init__.py
│   ├── vapi.py                 # VAPI API service functions
│   └── openai_service.py       # OpenAI API service functions
├── utils/
│   ├── __init__.py
│   └── prompt_parser.py        # Prompt parsing and manipulation utilities
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Getting Started

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:
```bash
streamlit run app.py
```

3. The app will open in your browser automatically (typically at `http://localhost:8501`)

### First Time Setup

1. **Configure API Keys**: 
   ```bash
   cp config.example.py config.py
   ```
   Then edit `config.py` and add your API keys:
   - **VAPI API Key**: You can find your API key in your [VAPI Dashboard](https://dashboard.vapi.ai)
   - **OpenAI API Key**: You can find your API key in your [OpenAI Platform](https://platform.openai.com/api-keys)
   
   **Note**: `config.py` is excluded from git for security. Never commit your actual API keys.

## Usage

### Managing Variables

1. Select an assistant from the dropdown
2. Go to the "Variables" tab
3. The app will automatically detect all variables in the format `{{variableName}}` from the system prompt
4. Enter values for variables (all fields are optional - only filled variables will be replaced)
5. Click "Update Variables" to save variable values
6. Click "Save Changes" at the bottom to update the assistant

### Managing FAQs

1. Select an assistant from the dropdown
2. Go to the "Custom FAQs" tab
3. Click "Add New FAQ" to create a new custom FAQ entry:
   - **User Trigger**: What the user might say (e.g., "What if I sold the car?")
   - **Bot Response Instruction**: How the bot should respond (e.g., "Acknowledge and transfer to agent")
4. Edit the OpenAI prompt template (optional) - use `{faqs}` as a placeholder
5. Click "Generate FAQ Prompt" to convert FAQs into a system prompt using OpenAI
6. Review the generated prompt
7. Click "Save Changes" at the bottom to append the FAQ prompt to the system prompt and update the assistant

## API Integration

### VAPI API
- Base URL: `https://api.vapi.ai`
- Authentication: Bearer token (API key)
- Endpoints:
  - `GET /assistant` - List all assistants
  - `GET /assistant/{id}` - Get assistant details
  - `PATCH /assistant/{id}` - Update assistant configuration

### OpenAI API
- Base URL: `https://api.openai.com/v1`
- Authentication: Bearer token (API key)
- Endpoint: `POST /chat/completions`
- Model: `gpt-4o-mini` (configurable in `services/openai_service.py`)

## Code Organization

The application is organized into modular components:

- **`app.py`**: Main Streamlit UI and orchestration
- **`config.py`**: All configuration constants and session state keys
- **`services/vapi.py`**: VAPI API integration functions
- **`services/openai_service.py`**: OpenAI API integration for FAQ prompt generation
- **`utils/prompt_parser.py`**: Utilities for parsing variables and manipulating prompts
