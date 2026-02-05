"""Variables management tab component."""

import streamlit as st
from config import VARIABLES_STORAGE_KEY


def render_variables_tab():
    """Render variables management tab."""
    st.header("Dynamic Variables")
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
