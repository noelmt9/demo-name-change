"""Explain Due section component."""

import streamlit as st
from config import SYSTEM_PROMPT_STORAGE_KEY, SELECTED_ASSISTANT_STORAGE_KEY
from services import activity_logger


def render_explain_due_section():
    """Render the EXPLAIN DUE FLOW first message section."""
    from services.openai_service import extract_explain_due_with_llm

    st.header("Explain Due First Message")
    st.markdown("View and update the first message from the EXPLAIN DUE FLOW section.")

    # Get current system prompt and assistant ID
    current_prompt = st.session_state.get(SYSTEM_PROMPT_STORAGE_KEY, "")
    current_assistant = st.session_state.get(SELECTED_ASSISTANT_STORAGE_KEY, {})
    current_assistant_id = current_assistant.get('id', '')

    if not current_prompt:
        st.info("No system prompt loaded. Please select an assistant first.")
        return

    # Check if EXPLAIN DUE FLOW section exists
    if "EXPLAIN DUE FLOW" not in current_prompt:
        st.info("This assistant does not have an EXPLAIN DUE FLOW section.")
        return

    # Simple cache: store assistant_id with the cached value to detect changes
    cache = st.session_state.get("explain_due_cache", {})
    cached_assistant_id = cache.get("assistant_id", "")

    # Check if cache is valid (same assistant)
    if cached_assistant_id != current_assistant_id:
        # Cache is stale or doesn't exist - need to extract
        with st.spinner("Extracting explain due message..."):
            try:
                current_explain_due = extract_explain_due_with_llm(current_prompt)
                # Store with assistant ID for validation
                st.session_state["explain_due_cache"] = {
                    "assistant_id": current_assistant_id,
                    "message": current_explain_due
                }
            except Exception as e:
                st.error(f"Failed to extract explain due message: {str(e)}")
                return
    else:
        # Use cached result
        current_explain_due = cache.get("message", "")

    if not current_explain_due:
        _render_debug_info(current_prompt)
        return

    # Display current explain due message
    with st.expander("Current Explain Due Message", expanded=True):
        st.text_area(
            "Current Message",
            value=current_explain_due,
            height=150,
            key=f"current_explain_due_display_{current_assistant_id}",
            disabled=True,
            help="This is the current first message from the EXPLAIN DUE FLOW section"
        )

    # Section to update the explain due message
    st.markdown("---")
    st.markdown("### Update Explain Due Message")
    st.markdown("*Changes here will only apply to new assistants you create, not the original template.*")

    # Initialize session state for pending explain due changes
    if "pending_explain_due" not in st.session_state:
        st.session_state["pending_explain_due"] = None

    # Tabs for paste vs generate
    tab1, tab2 = st.tabs(["Paste New Message", "Refine with AI"])

    with tab1:
        st.markdown("**Paste a new explain due message below:**")
        new_explain_due_paste = st.text_area(
            "New Explain Due Message",
            value="",
            height=150,
            key=f"new_explain_due_paste_{current_assistant_id}",
            placeholder="Paste your new explain due message here...",
            help="Enter the complete explain due message. This will be used when creating a new assistant."
        )

        if st.button("Preview Pasted Message", key="preview_paste", use_container_width=True):
            if new_explain_due_paste.strip():
                st.session_state["pending_explain_due"] = new_explain_due_paste.strip()
                st.rerun()
            else:
                st.error("Please enter a message before previewing.")

    with tab2:
        st.markdown("**Describe how you want to refine the current message:**")
        st.markdown("*The AI will only adjust grammar, tone, and phrasing - all factual details (amounts, dates, names) will be preserved.*")
        explain_due_instructions = st.text_area(
            "Refinement Instructions",
            value="",
            height=100,
            key=f"explain_due_instructions_{current_assistant_id}",
            placeholder="Example: Make it more friendly and empathetic, fix any grammar issues, make it sound more conversational...",
            help="Describe how you want to change the tone or phrasing. Factual details will remain unchanged."
        )

        if st.button("Refine with AI", key="refine_explain_due", use_container_width=True):
            if explain_due_instructions.strip():
                with st.spinner("Refining explain due message with AI..."):
                    try:
                        from services.openai_service import refine_explain_due_message
                        refined_message = refine_explain_due_message(current_explain_due, explain_due_instructions.strip())
                        st.session_state["pending_explain_due"] = refined_message

                        # Log explain due refinement
                        user_info = st.session_state.get("user", {})
                        try:
                            refinement_id = activity_logger.log_explain_due_refinement(
                                template_assistant_id=current_assistant_id,
                                user_email=user_info.get("email"),
                                original_message=current_explain_due,
                                refinement_instructions=explain_due_instructions.strip(),
                                refined_message=refined_message
                            )
                            st.session_state["last_explain_due_refinement_id"] = refinement_id
                        except Exception as log_error:
                            print(f"Warning: Failed to log explain due refinement: {log_error}")

                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to refine explain due message: {str(e)}")
            else:
                st.error("Please provide instructions before refining.")

    # Show preview of pending changes
    if st.session_state.get("pending_explain_due"):
        st.markdown("---")
        st.markdown("### Preview: New Explain Due Message")
        st.info("This message will be used when you create a new assistant. The original template remains unchanged.")

        st.text_area(
            "New Message (Preview)",
            value=st.session_state["pending_explain_due"],
            height=150,
            key=f"pending_explain_due_preview_{current_assistant_id}",
            disabled=True
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use This Message", key="accept_explain_due", use_container_width=True, type="primary"):
                # Store the pending message to be used when creating a new assistant
                st.session_state["accepted_explain_due"] = st.session_state["pending_explain_due"]
                st.session_state["pending_explain_due"] = None

                # Mark the refinement as accepted in the log
                refinement_id = st.session_state.get("last_explain_due_refinement_id")
                if refinement_id:
                    try:
                        activity_logger.mark_explain_due_accepted(refinement_id)
                    except Exception as log_error:
                        print(f"Warning: Failed to mark explain due as accepted: {log_error}")

                st.success("Message accepted! It will be used when you create a new assistant.")
                st.rerun()
        with col2:
            if st.button("Discard", key="discard_explain_due", use_container_width=True):
                st.session_state["pending_explain_due"] = None
                st.rerun()

    # Show accepted message if one exists
    if st.session_state.get("accepted_explain_due"):
        st.markdown("---")
        st.success("**Custom Explain Due Message Ready**")
        st.markdown("The following message will be used instead of the original when creating a new assistant:")
        st.text_area(
            "Accepted Custom Message",
            value=st.session_state["accepted_explain_due"],
            height=100,
            key=f"accepted_explain_due_display_{current_assistant_id}",
            disabled=True
        )
        if st.button("Remove Custom Message (Use Original)", key="remove_custom_explain_due"):
            st.session_state["accepted_explain_due"] = None
            st.success("Custom message removed. The original will be used.")
            st.rerun()


def _render_debug_info(current_prompt: str):
    """Render debug info when explain due extraction fails."""
    has_explain_due_text = "EXPLAIN DUE FLOW" in current_prompt
    prompt_length = len(current_prompt)

    st.warning("EXPLAIN DUE FLOW section not found in the system prompt.")

    with st.expander("Debug Info - Click to expand and share this info", expanded=False):
        st.text(f"System prompt length: {prompt_length} characters")
        st.text(f"Contains 'EXPLAIN DUE FLOW' text: {has_explain_due_text}")

        if has_explain_due_text:
            st.text("The text exists but extraction failed. Checking line format...")

            lines = current_prompt.split('\n')
            heading_line_num = None
            for i, line in enumerate(lines):
                if 'EXPLAIN DUE FLOW' in line and line.strip().startswith('#'):
                    heading_line_num = i
                    break

            if heading_line_num is not None:
                st.code(f"Heading line {heading_line_num}: {repr(lines[heading_line_num])}", language="python")

                st.text("\nNext 5 lines after heading:")
                for i in range(heading_line_num + 1, min(heading_line_num + 6, len(lines))):
                    st.code(f"Line {i}: {repr(lines[i][:80])}", language="python")

                import re
                pattern = r'^#{2,3}\s+EXPLAIN DUE FLOW[:\s]*$'
                match = re.match(pattern, lines[heading_line_num], re.IGNORECASE)
                st.text(f"\nRegex match result: {'MATCHED' if match else 'NO MATCH'}")

                st.text("\nAttempting manual extraction...")
                from utils.prompt_parser import extract_explain_due_flow
                test_result = extract_explain_due_flow(current_prompt)
                st.text(f"Manual extraction result: {len(test_result)} characters")
                if test_result:
                    st.text_area("Extracted content:", test_result[:500], height=100)
            else:
                st.text("Could not find heading line starting with #")
        else:
            st.text("This assistant does not have an EXPLAIN DUE FLOW section.")
            st.text(f"Assistant: {st.session_state.get(SELECTED_ASSISTANT_STORAGE_KEY, {}).get('name', 'Unknown')}")
