"""Main Streamlit application for VAPI Assistant Manager."""

import streamlit as st
import os
import copy
from typing import Dict, List

from config import (
    ASSISTANTS_STORAGE_KEY,
    SELECTED_ASSISTANT_STORAGE_KEY,
    VARIABLES_STORAGE_KEY,
    FAQS_STORAGE_KEY,
    SYSTEM_PROMPT_STORAGE_KEY,
    FAQ_PROMPT_STORAGE_KEY,
)

from services import vapi
from services import openai_service
from utils.prompt_parser import extract_variables, replace_variables, append_faq_prompt

# Page configuration
st.set_page_config(
    page_title="VAPI Assistant Manager",
    page_icon="🎙️",
    layout="wide"
)

# Initialize session state
if ASSISTANTS_STORAGE_KEY not in st.session_state:
    st.session_state[ASSISTANTS_STORAGE_KEY] = []
if SELECTED_ASSISTANT_STORAGE_KEY not in st.session_state:
    st.session_state[SELECTED_ASSISTANT_STORAGE_KEY] = None
if VARIABLES_STORAGE_KEY not in st.session_state:
    st.session_state[VARIABLES_STORAGE_KEY] = {}
if FAQS_STORAGE_KEY not in st.session_state:
    st.session_state[FAQS_STORAGE_KEY] = []
if SYSTEM_PROMPT_STORAGE_KEY not in st.session_state:
    st.session_state[SYSTEM_PROMPT_STORAGE_KEY] = ""
if FAQ_PROMPT_STORAGE_KEY not in st.session_state:
    st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
if "first_message" not in st.session_state:
    st.session_state["first_message"] = ""
if "editing_faq_index" not in st.session_state:
    st.session_state["editing_faq_index"] = None
# Note: Template removed - now using trained writing style from utils/prompt_training.py


def load_assistant_data(assistant_id: str):
    """Load assistant data and extract variables."""
    try:
        assistant = vapi.get_assistant(assistant_id)
        if not assistant:
            return
        
        st.session_state[SELECTED_ASSISTANT_STORAGE_KEY] = assistant
        
        # Extract system prompt
        prompt = assistant.get("model", {}).get("messages", [{}])[0].get("content", "")
        st.session_state[SYSTEM_PROMPT_STORAGE_KEY] = prompt
        
        # Extract firstMessage if it exists
        first_message = assistant.get("firstMessage", "")
        st.session_state["first_message"] = first_message
        
        # Extract variables from both system prompt and firstMessage
        prompt_vars = extract_variables(prompt)
        first_msg_vars = extract_variables(first_message) if first_message else []
        all_variable_names = list(set(prompt_vars + first_msg_vars))
        
        current_vars = st.session_state[VARIABLES_STORAGE_KEY].copy()
        # Preserve existing values, add new variables
        st.session_state[VARIABLES_STORAGE_KEY] = {
            name: current_vars.get(name, "") for name in all_variable_names
        }
        
        # Clear FAQ prompt when loading new assistant
        st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
        
    except Exception as e:
        st.error(f"Error loading assistant: {str(e)}")


def render_sidebar():
    """Render sidebar with settings."""
    with st.sidebar:
        st.header("Settings")
        
        if st.button("🔄 Refresh Assistants"):
            try:
                st.session_state[ASSISTANTS_STORAGE_KEY] = vapi.list_assistants(limit=500)
                st.success("Assistants refreshed!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.divider()


def render_variables_tab():
    """Render variables management tab."""
    st.header("📝 Dynamic Variables")
    st.markdown("Update the values for variables used in the system prompt and first message. All fields are optional.")
    
    variables = st.session_state[VARIABLES_STORAGE_KEY]
    
    # Show first message preview (read-only) if it exists
    first_message = st.session_state.get("first_message", "")
    if first_message:
        st.markdown("### First Message Preview")
        st.info(f"**Current first message:** {first_message}")
        st.markdown("*Variables in the first message will be automatically replaced when you save.*")
        st.markdown("---")
    
    if variables:
        st.markdown("### Variable Values")
        # Create form for variables (all optional)
        with st.form("variables_form", clear_on_submit=False):
            cols = st.columns(2)
            for i, (var_name, var_value) in enumerate(variables.items()):
                with cols[i % 2]:
                    st.text_input(
                        f"`{var_name}`",
                        value=var_value,
                        key=f"var_{var_name}",
                        help=f"Optional value for {{{{{var_name}}}}} (used in system prompt and first message)"
                    )
            
            submitted = st.form_submit_button("Update Variables", use_container_width=True)
            if submitted:
                # Read values from form inputs and update session state
                updated_variables = {}
                for var_name in variables.keys():
                    updated_variables[var_name] = st.session_state.get(f"var_{var_name}", "")
                st.session_state[VARIABLES_STORAGE_KEY] = updated_variables
                st.success("Variables updated!")
                st.rerun()
    else:
        st.info("No variables found in the system prompt or first message. Variables should be in the format: `{{variableName}}`")


def main():
    st.title("🎙️ VAPI Assistant Manager")
    st.markdown("Manage your voice assistant configurations")
    
    # Render sidebar
    render_sidebar()
    
    # Check if VAPI API key is set
    api_key = vapi.get_api_key()
    if not api_key:
        st.error("⚠️ VAPI API key is not configured. Please set VAPI_API_KEY in config.py or as an environment variable.")
        st.stop()
    
    # Debug info (only show first/last chars for security)
    if api_key:
        with st.sidebar:
            with st.expander("🔍 Debug Info", expanded=False):
                st.text(f"API Key loaded: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
                st.text(f"From env var: {'VAPI_API_KEY' in os.environ}")
                if 'VAPI_API_KEY' in os.environ:
                    env_key = os.environ['VAPI_API_KEY']
                    st.text(f"Env var value: {env_key[:4]}...{env_key[-4:]} (length: {len(env_key)})")
    
    # Load assistants if not loaded
    if not st.session_state[ASSISTANTS_STORAGE_KEY]:
        try:
            with st.spinner("Loading assistants..."):
                st.session_state[ASSISTANTS_STORAGE_KEY] = vapi.list_assistants(limit=500)
        except Exception as e:
            st.error(f"Failed to load assistants: {str(e)}")
            st.stop()
    
    # Assistant selector
    assistants = st.session_state[ASSISTANTS_STORAGE_KEY]
    if not assistants:
        st.warning("No assistants found. Make sure your API key is correct.")
        st.stop()
    
    assistant_options = {
        f"{asst.get('name', 'Unnamed')} ({asst.get('id', '')})": asst.get('id')
        for asst in assistants
    }
    
    selected_name = st.selectbox(
        "Select Assistant",
        options=list(assistant_options.keys()),
        key="assistant_selector"
    )
    
    selected_id = assistant_options[selected_name]
    
    # Load assistant data when selection changes
    current_assistant = st.session_state[SELECTED_ASSISTANT_STORAGE_KEY]
    if (current_assistant is None or current_assistant.get('id') != selected_id):
        with st.spinner("Loading assistant configuration..."):
            load_assistant_data(selected_id)
    
    if not st.session_state[SELECTED_ASSISTANT_STORAGE_KEY]:
        st.stop()
    
    # Main content - Variables tab
    render_variables_tab()
    
    # Create New Assistant Section
    st.divider()
    st.subheader("➕ Create New Assistant")
    st.markdown("Enter a name and create a new assistant with the current variables and settings.")
    
    assistant_name = st.text_input(
        "Assistant Name",
        key="new_assistant_name",
        placeholder="Enter a name for the new assistant",
        help="This name will be used to identify the assistant in VAPI"
    )
    
    # Optional Custom FAQs Section
    st.markdown("---")
    with st.expander("❓ Optional: Add Custom FAQs", expanded=False):
        st.markdown("**Optional:** Add custom FAQs that will be converted to a prompt using OpenAI. Leave empty if you don't need custom FAQs.")
        
        faqs = st.session_state[FAQS_STORAGE_KEY]
        
        # Add new FAQ - using a form directly (no nested expander)
        st.markdown("### ➕ Add New FAQ")
        with st.form("add_faq_form", clear_on_submit=True):
            new_trigger = st.text_input(
                "Question the user will ask", 
                key="new_faq_trigger", 
                help="The question or statement the user will make (e.g., 'What if I sold the car?')"
            )
            new_instruction = st.text_area(
                "How you want the bot to respond", 
                key="new_faq_instruction",
                help="The desired bot response behavior (e.g., 'Acknowledge and transfer to agent'). This will be embedded into the generated prompt."
            )
            if st.form_submit_button("Add FAQ", use_container_width=True):
                if new_trigger and new_instruction:
                    faqs.append({
                        "trigger": new_trigger.strip(),
                        "instruction": new_instruction.strip()
                    })
                    st.session_state[FAQS_STORAGE_KEY] = faqs
                    # Clear generated FAQ prompt since FAQs have changed
                    st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
                    st.success("FAQ added!")
                    st.rerun()
                else:
                    st.error("Please fill in both fields")
        
        st.markdown("---")
        
        # Display existing FAQs
        if not faqs:
            st.info("No custom FAQs yet. Add one using the form above, or leave this section empty.")
        else:
            st.subheader("Current FAQs")
            for i, faq in enumerate(faqs):
                with st.container():
                    # Check if this FAQ is being edited
                    is_editing = st.session_state.get("editing_faq_index") == i
                    
                    if is_editing:
                        # Show edit form
                        with st.form(f"edit_faq_form_{i}", clear_on_submit=False):
                            edited_trigger = st.text_input(
                                "Question the user will ask",
                                value=faq['trigger'],
                                key=f"edit_trigger_{i}",
                                help="The question or statement the user will make"
                            )
                            edited_instruction = st.text_area(
                                "How you want the bot to respond",
                                value=faq['instruction'],
                                key=f"edit_instruction_{i}",
                                help="The desired bot response behavior"
                            )
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("✅ Save", use_container_width=True):
                                    if edited_trigger.strip() and edited_instruction.strip():
                                        faqs[i] = {
                                            "trigger": edited_trigger.strip(),
                                            "instruction": edited_instruction.strip()
                                        }
                                        st.session_state[FAQS_STORAGE_KEY] = faqs
                                        st.session_state["editing_faq_index"] = None
                                        # Clear generated FAQ prompt since FAQs have changed
                                        st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
                                        st.success("FAQ updated! Regenerate the FAQ prompt to reflect changes.")
                                        st.rerun()
                                    else:
                                        st.error("Please fill in both fields")
                            with col2:
                                if st.form_submit_button("❌ Cancel", use_container_width=True):
                                    st.session_state["editing_faq_index"] = None
                                    st.rerun()
                    else:
                        # Show display view with edit/delete buttons
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**Question:** \"{faq['trigger']}\"")
                            st.markdown(f"**Bot Response:** {faq['instruction']}")
                        with col2:
                            col_edit, col_delete = st.columns(2)
                            with col_edit:
                                if st.button("✏️ Edit", key=f"edit_faq_{i}", use_container_width=True):
                                    st.session_state["editing_faq_index"] = i
                                    st.rerun()
                            with col_delete:
                                if st.button("🗑️ Delete", key=f"delete_faq_{i}", use_container_width=True):
                                    faqs.pop(i)
                                    st.session_state[FAQS_STORAGE_KEY] = faqs
                                    # If we deleted the FAQ that was being edited, clear edit state
                                    if st.session_state.get("editing_faq_index") == i:
                                        st.session_state["editing_faq_index"] = None
                                    # Adjust edit index if we deleted an FAQ before the one being edited
                                    elif st.session_state.get("editing_faq_index") is not None and st.session_state.get("editing_faq_index") > i:
                                        st.session_state["editing_faq_index"] = st.session_state["editing_faq_index"] - 1
                                    # Clear generated FAQ prompt since FAQs have changed
                                    st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
                                    st.rerun()
                        st.divider()
            
            # Generate FAQ Prompt Button
            st.markdown("---")
            st.subheader("Generate FAQ Prompt")
            st.markdown("The AI will automatically learn from **all** your imported system prompts and generate FAQ prompts that match your writing style, tone, and structure.")
            if st.button("🤖 Generate FAQ Prompt", type="primary", use_container_width=True, key="generate_faq_prompt_inline"):
                if not faqs:
                    st.error("Please add at least one FAQ before generating the prompt.")
                else:
                    try:
                        with st.spinner("Generating FAQ prompt with AI (using your writing style)..."):
                            generated_prompt = openai_service.generate_faq_prompt(faqs=faqs)
                            st.session_state[FAQ_PROMPT_STORAGE_KEY] = generated_prompt
                            st.success("FAQ prompt generated successfully using your trained writing style!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error generating FAQ prompt: {str(e)}")
            
            # Display generated FAQ prompt
            if st.session_state[FAQ_PROMPT_STORAGE_KEY]:
                st.markdown("---")
                st.subheader("Generated FAQ Prompt")
                st.text_area(
                    "Generated Prompt",
                    value=st.session_state[FAQ_PROMPT_STORAGE_KEY],
                    height=200,
                    key="generated_faq_prompt_display_inline",
                    help="This is the prompt generated by OpenAI. It will be appended to the system prompt when you create the assistant."
                )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💾 Create Assistant", type="primary", use_container_width=True):
            if not assistant_name or not assistant_name.strip():
                st.error("Please enter a name for the assistant.")
            else:
                try:
                    with st.spinner("Creating assistant..."):
                        # Get current assistant to use as template
                        current_assistant = st.session_state[SELECTED_ASSISTANT_STORAGE_KEY]
                        current_model = current_assistant.get("model", {}) if current_assistant else {}
                        
                        # Get current variable values from form inputs (in case user didn't click "Update Variables")
                        current_variables = st.session_state.get(VARIABLES_STORAGE_KEY, {}).copy()
                        for var_name in current_variables.keys():
                            form_value = st.session_state.get(f"var_{var_name}", "")
                            if form_value:  # Use form value if available, otherwise keep existing
                                current_variables[var_name] = form_value
                        
                        # Replace variables in prompt
                        updated_prompt = replace_variables(
                            st.session_state[SYSTEM_PROMPT_STORAGE_KEY],
                            current_variables
                        )
                        
                        # Append FAQ prompt if generated
                        if st.session_state[FAQ_PROMPT_STORAGE_KEY]:
                            updated_prompt = append_faq_prompt(
                                updated_prompt,
                                st.session_state[FAQ_PROMPT_STORAGE_KEY]
                            )
                        
                        # Replace variables in firstMessage (if it exists)
                        first_message = st.session_state.get("first_message", "")
                        updated_first_message = ""
                        if first_message:
                            updated_first_message = replace_variables(
                                first_message,
                                current_variables
                            )
                        
                        # Copy ALL configurations from the template assistant (deep copy to avoid reference issues)
                        # Exclude read-only fields and fields that should not be copied
                        fields_to_exclude = {
                            "id", "name", "createdAt", "updatedAt", "orgId",
                            "isServerUrlSecretSet",  # Read-only property
                            # Add other read-only properties that might cause issues
                        }
                        new_assistant_data = {}
                        for key, value in current_assistant.items():
                            if key not in fields_to_exclude:
                                # Deep copy nested structures
                                if isinstance(value, dict):
                                    new_assistant_data[key] = copy.deepcopy(value)
                                elif isinstance(value, list):
                                    new_assistant_data[key] = copy.deepcopy(value)
                                else:
                                    new_assistant_data[key] = value
                        
                        # Set the new name
                        new_assistant_data["name"] = assistant_name.strip()
                        
                        # Update model messages with the new prompt (variables replaced)
                        if "model" not in new_assistant_data:
                            new_assistant_data["model"] = {}
                        
                        existing_messages = new_assistant_data["model"].get("messages", [])
                        if existing_messages and len(existing_messages) > 0:
                            updated_messages = existing_messages.copy()
                            if updated_messages[0].get("role") == "system":
                                updated_messages[0] = {
                                    "role": "system",
                                    "content": updated_prompt
                                }
                            else:
                                updated_messages.insert(0, {
                                    "role": "system",
                                    "content": updated_prompt
                                })
                            new_assistant_data["model"]["messages"] = updated_messages
                        else:
                            new_assistant_data["model"]["messages"] = [
                                {
                                    "role": "system",
                                    "content": updated_prompt
                                }
                            ]
                        
                        # Update firstMessage with variables replaced (if original exists)
                        if first_message:  # If original firstMessage exists, always include it with variables replaced
                            new_assistant_data["firstMessage"] = updated_first_message
                        elif "firstMessage" in new_assistant_data:
                            # If template had firstMessage but current doesn't, remove it
                            del new_assistant_data["firstMessage"]
                        
                        # Create the assistant
                        new_assistant = vapi.create_assistant(new_assistant_data)
                        st.success(f"✅ Assistant '{assistant_name}' created successfully!")
                        
                        # Refresh assistants list
                        st.session_state[ASSISTANTS_STORAGE_KEY] = vapi.list_assistants(limit=500)
                        
                        # Select the new assistant
                        if new_assistant and new_assistant.get("id"):
                            load_assistant_data(new_assistant["id"])
                        
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to create assistant: {str(e)}")


if __name__ == "__main__":
    main()
