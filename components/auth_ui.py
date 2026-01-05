"""Authentication UI components for Streamlit."""

import streamlit as st
from services import auth


def render_logout_button():
    """Render logout button in sidebar."""
    user = auth.get_current_user()
    if user:
        with st.sidebar:
            st.divider()
            st.markdown(f"**Logged in as:** {user.get('name', user.get('email', 'User'))}")
            if st.button("🚪 Logout", use_container_width=True):
                auth.logout()
                st.rerun()
