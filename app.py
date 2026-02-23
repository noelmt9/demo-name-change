"""Main Streamlit application for VAPI Assistant Manager."""

import streamlit as st
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import (
    ASSISTANTS_STORAGE_KEY,
    SELECTED_ASSISTANT_STORAGE_KEY,
    VARIABLES_STORAGE_KEY,
    FAQS_STORAGE_KEY,
    SYSTEM_PROMPT_STORAGE_KEY,
    FAQ_PROMPT_STORAGE_KEY,
)

from services import vapi
from services import auth
from services import firebase_auth
from utils.prompt_parser import extract_variables
from components import auth_ui
from components.styles import inject_custom_css
from components.variables_tab import render_variables_tab
from components.explain_due_section import render_explain_due_section
from components.faq_section import render_faq_section
from components.assistant_creator import render_assistant_creator


def _get_logo_base64():
    """Load and encode the logo image as base64."""
    logo_path = Path(__file__).parent / "static" / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def is_local_environment():
    """Check if running in local development environment."""
    if os.getenv("BYPASS_AUTH", "").lower() in ("true", "1", "yes"):
        return True

    if not os.getenv("FIREBASE_LOGIN_PAGE_URL"):
        return True

    try:
        streamlit_url = os.getenv("STREAMLIT_APP_URL", "")
        if streamlit_url and "replit.app" in streamlit_url:
            return False
    except:
        pass

    return True


# Page configuration
st.set_page_config(
    page_title="VAPI Assistant Manager",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS
inject_custom_css()

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
if "last_created_assistant_name" not in st.session_state:
    st.session_state["last_created_assistant_name"] = None
if "last_used_training_examples" not in st.session_state:
    st.session_state["last_used_training_examples"] = None
if "last_loaded_assistant_id" not in st.session_state:
    st.session_state["last_loaded_assistant_id"] = None


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
        st.session_state[VARIABLES_STORAGE_KEY] = {
            name: current_vars.get(name, "") for name in all_variable_names
        }

        # Track the assistant ID we just loaded
        st.session_state["last_loaded_assistant_id"] = assistant_id

        # Clear all assistant-specific caches when loading new assistant
        st.session_state[FAQ_PROMPT_STORAGE_KEY] = ""
        st.session_state[FAQS_STORAGE_KEY] = []
        st.session_state["editing_faq_index"] = None
        st.session_state["explain_due_cache"] = {}

        # Clear the "assistant created" success message when switching assistants
        # BUT keep it if we just created this assistant
        created_info = st.session_state.get("last_created_assistant_info")
        if created_info and created_info.get("id") != assistant_id:
            st.session_state["last_created_assistant_info"] = None

    except Exception as e:
        st.error(f"Error loading assistant: {str(e)}")


def render_sidebar():
    """Render sidebar with settings."""
    with st.sidebar:
        st.header("Settings")

        if st.button("Refresh Assistants"):
            try:
                st.session_state[ASSISTANTS_STORAGE_KEY] = vapi.list_assistants(limit=500)
                st.success("Assistants refreshed!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

        st.divider()


def render_auth_page():
    """Render the authentication page."""
    login_page_url = os.getenv("FIREBASE_LOGIN_PAGE_URL", "https://vapi-assistant-builder-login.replit.app")
    return_to = os.getenv("STREAMLIT_APP_URL", "https://vapi-assistant-builder.replit.app")

    from urllib.parse import quote
    login_url = f"{login_page_url}?return_to={quote(return_to, safe='')}"

    logo_base64 = _get_logo_base64()
    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        background: #1a1a1a;
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    ">
        <div style="
            background: #1a1a1a;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 420px;
            text-align: center;
            border: 1px solid #4b5563;
        ">
            {f'<div style="margin-bottom: 2rem;"><img src="data:image/png;base64,{logo_base64}" style="height: 50px; width: auto; object-fit: contain;" alt="skit.ai logo" /></div>' if logo_base64 else ''}
            <h1 style="
                color: #ffffff;
                font-size: 1.75rem;
                font-weight: 700;
                margin-top: 0;
                margin-bottom: 0.5rem;
            ">Welcome Back</h1>
            <p style="
                color: #e5e7eb;
                font-size: 0.9rem;
                margin-bottom: 2rem;
            ">Sign in to access the VAPI Assistant Manager</p>
            <a href="{login_url}" style="
                display: inline-block;
                width: 100%;
                background: linear-gradient(135deg, #2D83C5 0%, #010066 100%);
                color: white;
                text-decoration: none;
                padding: 0.75rem 1.5rem;
                border-radius: 6px;
                font-size: 1rem;
                font-weight: 600;
                transition: all 0.2s;
                text-align: center;
            " onmouseover="this.style.background='linear-gradient(135deg, #010066 0%, #2D83C5 100%)'" onmouseout="this.style.background='linear-gradient(135deg, #2D83C5 0%, #010066 100%)'">
                Continue to Login Page
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def handle_authentication():
    """Handle authentication flow. Returns True if authenticated."""
    if is_local_environment():
        if "user" not in st.session_state:
            st.session_state["user"] = {
                "email": "local@dev.local",
                "name": "Local Developer",
                "uid": "local-dev-user",
                "auth_method": "local",
                "email_verified": True
            }
        return True

    import streamlit.components.v1 as components

    # Step 1: Handle tokens from URL (from login redirect)
    id_token = st.query_params.get("id_token")
    refresh_token = st.query_params.get("refresh_token")

    if id_token:
        try:
            firebase_auth.initialize_firebase_admin()
            if firebase_auth.is_firebase_admin_available():
                from firebase_admin import auth as fb_auth
                decoded = fb_auth.verify_id_token(id_token)

                # Store user in session state (for this page load)
                st.session_state["user"] = {
                    "email": decoded.get("email"),
                    "name": decoded.get("name", decoded.get("email", "").split("@")[0]),
                    "uid": decoded.get("uid"),
                    "auth_method": "google" if decoded.get("firebase", {}).get("sign_in_provider") == "google.com" else "email",
                    "id_token": id_token,
                    "refresh_token": refresh_token,
                    "email_verified": decoded.get("email_verified", False)
                }

                # Store ONLY refresh_token in localStorage (persists across refreshes)
                if refresh_token:
                    components.html(f"""
                    <script>
                        localStorage.setItem('firebase_refresh_token', '{refresh_token}');
                        console.log('Stored refresh token in localStorage');
                    </script>
                    """, height=0)

                # Clear query params
                st.query_params.clear()
                st.success(f"Welcome, {st.session_state['user']['name']}!")
                st.rerun()
            else:
                st.error("Firebase Admin SDK not initialized.")
        except Exception as e:
            st.error(f"Failed to verify token: {str(e)}")
            st.query_params.clear()

    # Step 2: Try to restore session using refresh_token from localStorage
    restore_token = st.query_params.get("restore_token")

    if restore_token and "user" not in st.session_state:
        # We have a refresh token from localStorage, use it to get a new session
        try:
            refreshed_data = firebase_auth.refresh_user_token(restore_token)
            if refreshed_data:
                firebase_auth.initialize_firebase_admin()
                if firebase_auth.is_firebase_admin_available():
                    from firebase_admin import auth as fb_auth
                    # Verify the new ID token
                    decoded = fb_auth.verify_id_token(refreshed_data["id_token"])

                    st.session_state["user"] = {
                        "email": decoded.get("email"),
                        "name": decoded.get("name", decoded.get("email", "").split("@")[0]),
                        "uid": decoded.get("uid"),
                        "auth_method": refreshed_data.get("auth_method", "google"),
                        "id_token": refreshed_data["id_token"],
                        "refresh_token": refreshed_data.get("refresh_token", restore_token),
                        "email_verified": decoded.get("email_verified", False)
                    }

                    # Clear the restore_token from URL
                    st.query_params.clear()
                    st.rerun()
        except Exception as e:
            # Refresh failed, clear localStorage and show login
            components.html("""
            <script>
                localStorage.removeItem('firebase_refresh_token');
            </script>
            """, height=0)
            st.query_params.clear()

    # Step 3: If no user in session, inject script to check localStorage
    if "user" not in st.session_state:
        components.html("""
        <script>
            const refreshToken = localStorage.getItem('firebase_refresh_token');
            const urlParams = new URLSearchParams(window.location.search);
            const hasRestoreToken = urlParams.get('restore_token');

            if (refreshToken && !hasRestoreToken) {
                // Redirect with refresh token to restore session
                window.location.href = window.location.pathname + '?restore_token=' + refreshToken;
            }
        </script>
        """, height=0)

    # Step 4: Check authentication - but DON'T verify token on every call
    if "user" not in st.session_state:
        render_auth_page()
        st.stop()
        return False

    return True


def render_header():
    """Render the main header with logo."""
    st.markdown("""
    <div class="main-header">
        <div class="logo-container">
            <img src="data:image/png;base64,{}" class="logo-img" alt="skit.ai logo" />
        </div>
    </div>
    """.format(_get_logo_base64()), unsafe_allow_html=True)

    st.markdown("## VAPI Assistant Manager")
    st.markdown("Manage your voice assistant configurations")


def render_assistant_selector():
    """Render the assistant selector dropdown."""
    assistants = st.session_state[ASSISTANTS_STORAGE_KEY]

    # Filter assistants to only include those with "API" in the name
    filtered_assistants = [
        asst for asst in assistants
        if asst.get('name', '').upper().find('API') != -1
    ]

    if not filtered_assistants:
        st.warning("No assistants found with 'API' in the name.")
        st.stop()

    assistant_options = {
        f"{asst.get('name', 'Unnamed')} ({asst.get('id', '')})": asst.get('id')
        for asst in filtered_assistants
    }

    current_assistant = st.session_state.get(SELECTED_ASSISTANT_STORAGE_KEY)
    current_id = current_assistant.get('id') if current_assistant else None

    default_index = 0
    if current_id:
        for idx, (name, asst_id) in enumerate(assistant_options.items()):
            if asst_id == current_id:
                default_index = idx
                break

    st.session_state["_assistant_options"] = assistant_options

    def on_assistant_change():
        selected_name = st.session_state.assistant_selector
        options = st.session_state.get("_assistant_options", {})
        if selected_name in options:
            new_id = options[selected_name]
            load_assistant_data(new_id)

    selected_name = st.selectbox(
        "Select Assistant",
        options=list(assistant_options.keys()),
        index=default_index,
        key="assistant_selector",
        on_change=on_assistant_change
    )

    selected_id = assistant_options[selected_name]

    # Load assistant data on first load
    if current_assistant is None:
        with st.spinner("Loading assistant configuration..."):
            load_assistant_data(selected_id)
            st.rerun()


def main():
    """Main application entry point."""
    # Handle authentication
    if not handle_authentication():
        return

    # Render header and logout button
    render_header()
    auth_ui.render_logout_button()
    render_sidebar()

    # Check if VAPI API key is set
    api_key = vapi.get_api_key()
    if not api_key:
        st.error("VAPI API key is not configured. Please set VAPI_API_KEY in config.py or as an environment variable.")
        st.stop()

    # Debug info in sidebar
    if api_key:
        with st.sidebar:
            with st.expander("Debug Info", expanded=False):
                st.text(f"API Key loaded: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
                st.text(f"From env var: {'VAPI_API_KEY' in os.environ}")

    # Load assistants if not loaded
    if not st.session_state[ASSISTANTS_STORAGE_KEY]:
        try:
            with st.spinner("Loading assistants..."):
                st.session_state[ASSISTANTS_STORAGE_KEY] = vapi.list_assistants(limit=500)
        except Exception as e:
            st.error(f"Failed to load assistants: {str(e)}")
            st.stop()

    assistants = st.session_state[ASSISTANTS_STORAGE_KEY]
    if not assistants:
        st.warning("No assistants found. Make sure your API key is correct.")
        st.stop()

    # Render assistant selector
    render_assistant_selector()

    if not st.session_state[SELECTED_ASSISTANT_STORAGE_KEY]:
        st.stop()

    # Render main content sections
    render_variables_tab()

    st.divider()
    render_explain_due_section()

    st.divider()
    render_faq_section()

    st.divider()
    render_assistant_creator(load_assistant_data)


if __name__ == "__main__":
    main()
