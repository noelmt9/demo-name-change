"""Assistant creation component."""

import copy
import streamlit as st
from config import (
    ASSISTANTS_STORAGE_KEY,
    SELECTED_ASSISTANT_STORAGE_KEY,
    VARIABLES_STORAGE_KEY,
    SYSTEM_PROMPT_STORAGE_KEY,
    FAQ_PROMPT_STORAGE_KEY,
)
from services import vapi
from services import activity_logger
from services.openai_service import replace_explain_due_with_llm
from utils.prompt_parser import replace_variables, append_faq_prompt


def render_assistant_creator(load_assistant_data_func):
    """
    Render the assistant creation section.

    Args:
        load_assistant_data_func: Function to call to load assistant data after creation
    """
    st.subheader("Create New Assistant")
    st.markdown("Enter a name and create a new assistant with the current variables and settings.")

    # Display persistent success message if an assistant was just created
    _render_success_message()

    assistant_name = st.text_input(
        "Assistant Name",
        key="new_assistant_name",
        placeholder="Enter a name for the new assistant",
        help="This name will be used to identify the assistant in VAPI"
    )

    # Retention period selector
    st.markdown("---")
    st.markdown("### Retention Period")
    st.markdown("*Choose how long to keep this assistant. Default is 2 weeks.*")

    retention_options = {
        "2 weeks (default)": 14,
        "3 weeks": 21,
        "4 weeks": 28,
        "5 weeks": 35,
        "6 weeks": 42
    }

    selected_retention = st.selectbox(
        "Retention Period",
        options=list(retention_options.keys()),
        index=0,
        key="retention_selector",
        help="Select how long to keep this assistant before it's eligible for cleanup (max 6 weeks)"
    )

    retention_days = retention_options[selected_retention]

    st.caption(f"This assistant will be auto-removed after {selected_retention.replace(' (default)', '')} if not renewed.")

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Create Assistant", type="primary", use_container_width=True):
            _create_assistant(assistant_name, retention_days, load_assistant_data_func)


def _render_success_message():
    """Render the success message after assistant creation."""
    created_info = st.session_state.get("last_created_assistant_info")
    current_assistant_id = st.session_state.get(SELECTED_ASSISTANT_STORAGE_KEY, {}).get("id")

    if created_info and (created_info.get("id") == current_assistant_id or created_info.get("template_id") == current_assistant_id):
        st.success(f"Assistant '{created_info['name']}' created successfully!")
        st.markdown("---")
        st.markdown("### Assistant Created")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Assistant Name:** `{created_info['name']}`")
        with col2:
            call_url = "https://llm-studio.skit.ai/experience-assistant?region=us"
            st.link_button("Call Agent", call_url, use_container_width=True)
        st.markdown("---")

        if st.button("Dismiss", key="dismiss_success"):
            st.session_state["last_created_assistant_info"] = None
            st.rerun()


def _create_assistant(assistant_name: str, retention_days: int, load_assistant_data_func):
    """Create a new assistant with the given name and retention period."""
    if not assistant_name or not assistant_name.strip():
        st.error("Please enter a name for the assistant.")
        return

    try:
        with st.spinner("Creating assistant..."):
            current_assistant = st.session_state[SELECTED_ASSISTANT_STORAGE_KEY]
            current_model = current_assistant.get("model", {}) if current_assistant else {}

            # Get current variable values
            current_variables = st.session_state.get(VARIABLES_STORAGE_KEY, {}).copy()
            for var_name in current_variables.keys():
                form_value = st.session_state.get(f"var_{var_name}", "")
                if form_value:
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

            # Apply custom explain due message if one was accepted
            if st.session_state.get("accepted_explain_due"):
                explain_due_cache = st.session_state.get("explain_due_cache", {})
                original_explain_due = explain_due_cache.get("message", "")
                if original_explain_due:
                    updated_prompt = replace_explain_due_with_llm(
                        updated_prompt,
                        original_explain_due,
                        st.session_state["accepted_explain_due"]
                    )

            # Replace variables in firstMessage
            first_message = st.session_state.get("first_message", "")
            updated_first_message = ""
            if first_message:
                updated_first_message = replace_variables(first_message, current_variables)

            # Copy configurations from template assistant
            fields_to_exclude = {
                "id", "name", "createdAt", "updatedAt", "orgId",
                "isServerUrlSecretSet",
            }
            new_assistant_data = {}
            for key, value in current_assistant.items():
                if key not in fields_to_exclude:
                    if isinstance(value, dict):
                        new_assistant_data[key] = copy.deepcopy(value)
                    elif isinstance(value, list):
                        new_assistant_data[key] = copy.deepcopy(value)
                    else:
                        new_assistant_data[key] = value

            # Set the new name
            new_assistant_data["name"] = assistant_name.strip()

            # Update model messages with the new prompt
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

            # Update firstMessage
            if first_message:
                new_assistant_data["firstMessage"] = updated_first_message
            elif "firstMessage" in new_assistant_data:
                del new_assistant_data["firstMessage"]

            # Create the assistant
            new_assistant = vapi.create_assistant(new_assistant_data)

            # Store success info
            created_name = assistant_name.strip()
            st.session_state["last_created_assistant_info"] = {
                "name": created_name,
                "id": new_assistant.get("id") if new_assistant else None,
                "template_id": current_assistant.get("id")
            }

            # Log the assistant creation
            user_info = st.session_state.get("user", {})
            try:
                activity_logger.log_assistant_creation(
                    vapi_assistant_id=new_assistant.get("id", ""),
                    assistant_name=created_name,
                    template_assistant_id=current_assistant.get("id"),
                    user_email=user_info.get("email"),
                    user_id=user_info.get("uid"),
                    variables=current_variables,
                    faq_prompt=st.session_state.get(FAQ_PROMPT_STORAGE_KEY),
                    explain_due_message=st.session_state.get("accepted_explain_due"),
                    retention_days=retention_days
                )
            except Exception as log_error:
                print(f"Warning: Failed to log assistant creation: {log_error}")

            # Mark FAQ as accepted if one was used
            if st.session_state.get(FAQ_PROMPT_STORAGE_KEY):
                faq_gen_id = st.session_state.get("last_faq_generation_id")
                if faq_gen_id:
                    try:
                        activity_logger.mark_faq_accepted(faq_gen_id)
                    except Exception as log_error:
                        print(f"Warning: Failed to mark FAQ as accepted: {log_error}")

            # Clear custom explain due after successful creation
            st.session_state["accepted_explain_due"] = None
            st.session_state["pending_explain_due"] = None

            # Refresh assistants list
            st.session_state[ASSISTANTS_STORAGE_KEY] = vapi.list_assistants(limit=500)

            # Select the new assistant
            if new_assistant and new_assistant.get("id"):
                load_assistant_data_func(new_assistant["id"])

            st.rerun()
    except Exception as e:
        st.error(f"Failed to create assistant: {str(e)}")
