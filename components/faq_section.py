"""FAQ section component."""

import streamlit as st
from config import (
    SYSTEM_PROMPT_STORAGE_KEY,
    SELECTED_ASSISTANT_STORAGE_KEY,
    FAQS_STORAGE_KEY,
    FAQ_PROMPT_STORAGE_KEY,
)
from services import faq_generator
from services import activity_logger
from utils.prompt_parser import extract_flows, extract_existing_faq_section, count_existing_faqs


def render_faq_section():
    """Render the FAQ section with existing FAQs and custom FAQ input."""
    existing_prompt = st.session_state.get(SYSTEM_PROMPT_STORAGE_KEY, "")
    current_asst = st.session_state.get(SELECTED_ASSISTANT_STORAGE_KEY, {})
    current_asst_id = current_asst.get('id', '') if current_asst else ''

    # Show existing FAQ context
    with st.expander("View Existing FAQ Context", expanded=True):
        if existing_prompt:
            available_flows = extract_flows(existing_prompt)
            existing_faqs = extract_existing_faq_section(existing_prompt)
            existing_faq_count = count_existing_faqs(existing_prompt)

            if existing_faqs:
                st.markdown(f"**Existing FAQ Section:** ({existing_faq_count} FAQ{'s' if existing_faq_count != 1 else ''} found)")
                st.text_area(
                    "Existing FAQs",
                    value=existing_faqs,
                    height=150,
                    key=f"existing_faqs_display_{current_asst_id}",
                    disabled=True,
                    help=f"These {existing_faq_count} FAQ(s) already exist in the prompt. Your new FAQs will be appended and numbered starting from {existing_faq_count + 1}."
                )
            else:
                st.info("No existing FAQ section found. This will be the first FAQ section.")
        else:
            st.warning("No assistant loaded. Please select an assistant from the sidebar to see existing FAQs.")
            st.info("Once you load an assistant, this section will show existing FAQ sections (if any).")

    # Optional Custom FAQs Section
    st.markdown("---")
    with st.expander("Optional: Add Custom FAQs", expanded=False):
        st.markdown("**Optional:** Add custom FAQs that will be converted to a prompt using OpenAI. Leave empty if you don't need custom FAQs.")

        faqs = st.session_state[FAQS_STORAGE_KEY]

        # Add new FAQ
        st.markdown("### Add New FAQ")
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
            _render_faq_list(faqs, existing_prompt, current_asst_id)


def _render_faq_list(faqs: list, existing_prompt: str, current_asst_id: str):
    """Render the list of FAQs with edit/delete functionality."""
    for i, faq in enumerate(faqs):
        with st.container():
            is_editing = st.session_state.get("editing_faq_index") == i

            if is_editing:
                _render_faq_edit_form(i, faq, faqs)
            else:
                _render_faq_display(i, faq, faqs)
            st.divider()

    # Generate FAQ Prompt Button
    st.markdown("---")
    st.subheader("Generate FAQ Prompt")

    if st.button("Generate FAQ Prompt", type="primary", use_container_width=True, key="generate_faq_prompt_inline"):
        if not faqs:
            st.error("Please add at least one FAQ before generating the prompt.")
        else:
            _generate_faq_prompt(faqs, existing_prompt, current_asst_id)

    # Display generated FAQ prompt
    if st.session_state[FAQ_PROMPT_STORAGE_KEY]:
        st.markdown("---")
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.subheader("Generated FAQ Prompt")
        with col_header2:
            if st.button("Regenerate", key="regenerate_faq_prompt", use_container_width=True):
                _generate_faq_prompt(faqs, existing_prompt, current_asst_id, regenerate=True)

        st.text_area(
            "Generated Prompt",
            value=st.session_state[FAQ_PROMPT_STORAGE_KEY],
            height=200,
            key="generated_faq_prompt_display_inline",
            help="This prompt will be appended to the system prompt when you create the assistant."
        )


def _render_faq_edit_form(index: int, faq: dict, faqs: list):
    """Render edit form for a FAQ."""
    with st.form(f"edit_faq_form_{index}", clear_on_submit=False):
        edited_trigger = st.text_input(
            "Question the user will ask",
            value=faq['trigger'],
            key=f"edit_trigger_{index}",
            help="The question or statement the user will make"
        )
        edited_instruction = st.text_area(
            "How you want the bot to respond",
            value=faq['instruction'],
            key=f"edit_instruction_{index}",
            help="The desired bot response behavior"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save", use_container_width=True):
                if edited_trigger.strip() and edited_instruction.strip():
                    faqs[index] = {
                        "trigger": edited_trigger.strip(),
                        "instruction": edited_instruction.strip()
                    }
                    st.session_state[FAQS_STORAGE_KEY] = faqs
                    st.session_state["editing_faq_index"] = None
                    st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
                    st.success("FAQ updated! Regenerate the FAQ prompt to reflect changes.")
                    st.rerun()
                else:
                    st.error("Please fill in both fields")
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state["editing_faq_index"] = None
                st.rerun()


def _render_faq_display(index: int, faq: dict, faqs: list):
    """Render display view for a FAQ with edit/delete buttons."""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**Question:** \"{faq['trigger']}\"")
        st.markdown(f"**Bot Response:** {faq['instruction']}")
    with col2:
        col_edit, col_delete = st.columns(2)
        with col_edit:
            if st.button("Edit", key=f"edit_faq_{index}", use_container_width=True):
                st.session_state["editing_faq_index"] = index
                st.rerun()
        with col_delete:
            if st.button("Delete", key=f"delete_faq_{index}", use_container_width=True):
                faqs.pop(index)
                st.session_state[FAQS_STORAGE_KEY] = faqs
                if st.session_state.get("editing_faq_index") == index:
                    st.session_state["editing_faq_index"] = None
                elif st.session_state.get("editing_faq_index") is not None and st.session_state.get("editing_faq_index") > index:
                    st.session_state["editing_faq_index"] = st.session_state["editing_faq_index"] - 1
                st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
                st.rerun()


def _generate_faq_prompt(faqs: list, existing_prompt: str, current_asst_id: str, regenerate: bool = False):
    """Generate or regenerate FAQ prompt."""
    try:
        action = "Regenerating" if regenerate else "Generating"
        with st.spinner(f"{action} FAQ prompt..."):
            generated_prompt = faq_generator.generate_faqs(
                faqs=faqs,
                existing_prompt=existing_prompt if existing_prompt else None
            )
            st.session_state[FAQ_PROMPT_STORAGE_KEY] = generated_prompt

            # Log FAQ generation
            user_info = st.session_state.get("user", {})
            try:
                faq_gen_id = activity_logger.log_faq_generation(
                    template_assistant_id=current_asst_id,
                    user_email=user_info.get("email"),
                    input_faqs=faqs,
                    generated_prompt=generated_prompt
                )
                st.session_state["last_faq_generation_id"] = faq_gen_id
            except Exception as log_error:
                print(f"Warning: Failed to log FAQ generation: {log_error}")

            st.success(f"FAQ prompt {'regenerated' if regenerate else 'generated'} successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Error generating FAQ prompt: {str(e)}")
