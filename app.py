"""Main Streamlit application for VAPI Assistant Manager."""

import streamlit as st
import os
import copy
import base64
from pathlib import Path
from typing import Dict, List
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
from services import openai_service
from services import faq_generator
from services import auth
from services import firebase_auth
from utils.prompt_parser import extract_variables, replace_variables, append_faq_prompt
from components import auth_ui


def _get_logo_base64():
    """Load and encode the logo image as base64."""
    logo_path = Path(__file__).parent / "static" / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def is_local_environment():
    """Check if running in local development environment."""
    # Check environment variable for explicit local bypass
    if os.getenv("BYPASS_AUTH", "").lower() in ("true", "1", "yes"):
        return True
    
    # Check if FIREBASE_LOGIN_PAGE_URL is not set (indicates local dev)
    if not os.getenv("FIREBASE_LOGIN_PAGE_URL"):
        return True
    
    # Check if running on localhost (common for local Streamlit)
    # Streamlit typically runs on localhost:8501
    try:
        # Try to detect if we're on a Replit domain
        # If STREAMLIT_APP_URL is set and contains 'replit.app', we're on Replit
        streamlit_url = os.getenv("STREAMLIT_APP_URL", "")
        if streamlit_url and "replit.app" in streamlit_url:
            return False
    except:
        pass
    
    # Default: assume local if no Replit indicators found
    # This is safe because Replit should have env vars set
    return True

# Page configuration
st.set_page_config(
    page_title="VAPI Assistant Manager",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS for Skit.ai branding
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@200;300;400;500;600;700;800&display=swap');
    
    /* Apply Manrope font to all elements */
    * {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Grayish black background */
    .stApp {
        background: #1a1a1a;
    }
    
    /* Header with logo */
    .main-header {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        position: relative;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%);
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .logo-img {
        height: 45px;
        width: auto;
        object-fit: contain;
        display: block;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: #1a1a1a;
        border-radius: 8px;
    }
    
    /* Title styling with brand colors */
    h1 {
        color: #ffffff;
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Text color for readability on dark background */
    p, label, .stMarkdown {
        color: #e5e7eb;
    }
    
    /* Primary button styling - brand blue */
    .stButton > button {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        box-shadow: 0 2px 8px rgba(1, 0, 102, 0.3);
        color: white !important;
    }
    
    /* Secondary button styling */
    button[kind="secondary"] {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
        border: none;
    }
    
    button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        color: white !important;
    }
    
    /* All buttons should have white text */
    button {
        color: white !important;
    }
    
    /* Ensure all button text is white */
    .stButton > button,
    button[type="button"],
    button[type="submit"],
    .stFormSubmitButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        color: white !important;
    }
    
    button[type="button"] {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
    }
    
    button[type="button"]:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        color: white !important;
    }
    
    /* Ensure button text stays white on hover */
    .stButton > button:hover,
    button[type="button"]:hover,
    button[type="submit"]:hover,
    .stFormSubmitButton > button:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        color: white !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        border: 1px solid #4b5563;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        color: #ffffff !important;
        background-color: #2d2d2d !important;
    }
    
    /* Disabled textarea styling - ensure text is visible */
    .stTextArea > div > div > textarea:disabled {
        color: #e5e7eb !important;
        background-color: #2d2d2d !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #e5e7eb !important;
    }
    
    /* Fix textarea label and content overlap (Replit-specific fix) */
    .stTextArea label {
        position: relative !important;
        z-index: 1 !important;
        display: block !important;
        margin-bottom: 0.5rem !important;
        padding: 0 !important;
        line-height: 1.4 !important;
    }
    
    .stTextArea > div {
        position: relative !important;
        overflow: visible !important;
    }
    
    .stTextArea > div > div {
        position: relative !important;
        overflow: visible !important;
    }
    
    .stTextArea > div > div > textarea {
        position: relative !important;
        z-index: 1 !important;
        background-color: #2d2d2d !important;
        padding: 0.5rem 0.75rem !important;
        line-height: 1.5 !important;
        overflow-y: auto !important;
    }
    
    /* Hide any placeholder or key text that might show through */
    .stTextArea > div > div > textarea::placeholder {
        opacity: 0 !important;
        color: transparent !important;
    }
    
    /* Ensure no text overlap in disabled textareas */
    .stTextArea > div > div > textarea:disabled {
        position: relative !important;
        z-index: 1 !important;
        background-color: #2d2d2d !important;
        -webkit-text-fill-color: #e5e7eb !important;
        color: #e5e7eb !important;
        opacity: 1 !important;
        padding: 0.5rem 0.75rem !important;
        line-height: 1.5 !important;
    }
    
    /* Fix any Streamlit internal text that might be showing */
    div[data-testid="stTextArea"] label,
    div[data-testid="stTextArea"] > div > label,
    div[data-testid="stTextArea"] > div > div > label {
        position: relative !important;
        z-index: 2 !important;
        background-color: transparent !important;
        display: block !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Additional Replit-specific fixes - prevent any overlay text */
    .stTextArea [class*="label"],
    .stTextArea [class*="Label"] {
        position: relative !important;
        z-index: 2 !important;
        background: transparent !important;
        pointer-events: none !important;
    }

    /* Ensure textarea content is on top */
    .stTextArea textarea {
        position: relative !important;
        z-index: 3 !important;
        background: #2d2d2d !important;
    }

    /* CRITICAL FIX: Prevent text overlap in expander sections (Replit-specific) */
    .stExpander {
        isolation: isolate !important;
        position: relative !important;
        clear: both !important;
        overflow: visible !important;
    }

    /* Ensure expander header has proper spacing and doesn't overlap content */
    .stExpander summary {
        padding: 0.75rem 0 !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
        clear: both !important;
    }

    /* Ensure expander content container has proper isolation and spacing */
    .stExpander > div,
    .stExpander details,
    .stExpander [data-testid="stExpanderDetails"] {
        isolation: isolate !important;
        position: relative !important;
        z-index: 1 !important;
        clear: both !important;
        overflow: visible !important;
        padding-top: 0.5rem !important;
    }

    /* Prevent any absolute/fixed positioned children from escaping */
    .stExpander * {
        max-width: 100% !important;
    }

    /* Fix for overlapping labels in expander context */
    .stExpander label {
        display: block !important;
        position: relative !important;
        z-index: auto !important;
        margin-bottom: 0.5rem !important;
        clear: both !important;
        width: 100% !important;
        line-height: 1.5 !important;
    }

    /* Ensure all form elements inside expanders have proper spacing */
    .stExpander .stTextArea,
    .stExpander .stTextInput,
    .stExpander .stSelectbox {
        margin-top: 0.5rem !important;
        margin-bottom: 0.75rem !important;
        display: block !important;
        width: 100% !important;
        clear: both !important;
    }

    /* Remove any pseudo-elements that might cause overlap */
    .stTextArea::before,
    .stTextArea::after,
    .stTextArea > div::before,
    .stTextArea > div::after {
        display: none !important;
        content: none !important;
    }

    /* CRITICAL: Hide any keyboard hints, dev IDs, or debugging text that might show */
    [class*="keyboard"],
    [id*="keyboard"],
    [data-keyboard],
    [class*="hint"],
    [class*="debug"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }

    /* Prevent any aria-labels or titles from rendering as visible text */
    [aria-label]::before,
    [aria-label]::after,
    [title]::before,
    [title]::after {
        content: none !important;
        display: none !important;
    }

    /* Ensure Streamlit key identifiers don't render visibly */
    [data-testid]::before,
    [data-testid]::after {
        content: none !important;
        display: none !important;
    }
    
    /* HIDE expander arrow icon completely to prevent bleed-through */
    /* Target the icon using data-testid and all possible selectors */
    [data-testid="stIconMaterial"],
    .stExpander summary span[data-testid="stIconMaterial"],
    .stExpander summary [class*="Material"],
    .stExpander summary [class*="arrow"],
    span[data-testid="stIconMaterial"][translate="no"],
    .st-emotion-cache-zkd0x0,
    .ejhh0er0,
    span[color="inherit"][data-testid="stIconMaterial"],
    .stExpander [translate="no"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    
    /* Ensure expander header/summary doesn't interfere */
    .stExpander summary,
    .stExpander [data-testid="stExpander"] summary {
        z-index: 0 !important;
        position: relative !important;
    }
    
    /* Ensure expander details container has proper stacking */
    .stExpander [data-testid="stExpanderDetails"],
    .stExpander details > div {
        position: relative !important;
        z-index: 100 !important;
        isolation: isolate !important; /* Creates new stacking context */
        background: #1a1a1a !important; /* Solid background to cover any bleed-through */
    }

    /* Force all expander content to be above the arrow icon */
    .stExpander [data-testid="stExpanderDetails"] *,
    .stExpander details > div * {
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Ensure textarea content is above expander icons */
    .stTextArea > div > div > textarea,
    .stTextArea > div > div > textarea:disabled {
        z-index: 10 !important;
        position: relative !important;
        background-color: #2d2d2d !important;
        isolation: isolate !important; /* Creates new stacking context */
    }
    
    /* Ensure textarea container is above expander elements */
    .stTextArea,
    .stTextArea > div,
    .stTextArea > div > div {
        z-index: 5 !important;
        position: relative !important;
    }
    
    /* Additional fix: ensure expander details content is isolated */
    .stExpander [data-testid="stExpanderDetails"] .stTextArea {
        position: relative !important;
        z-index: 2 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #2D83C5;
        box-shadow: 0 0 0 3px rgba(45, 131, 197, 0.3);
        color: #ffffff !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #1a1a1a;
    }
    
    /* Links */
    a {
        color: #2D83C5;
    }
    
    a:hover {
        color: #010066;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #1a1a1a !important;
        border: 1px solid #10b981;
        color: #e5e7eb !important;
    }
    
    .stSuccess * {
        color: #e5e7eb !important;
    }
    
    .stError {
        background-color: #1a1a1a !important;
        border: 1px solid #ef4444;
        color: #e5e7eb !important;
    }
    
    .stError * {
        color: #e5e7eb !important;
    }
    
    .stInfo {
        background-color: #1a1a1a !important;
        border: 1px solid #2D83C5;
        color: #e5e7eb !important;
    }
    
    .stInfo * {
        color: #e5e7eb !important;
    }
    
    .stWarning {
        background-color: #1a1a1a !important;
        border: 1px solid #f59e0b;
        color: #e5e7eb !important;
    }
    
    .stWarning * {
        color: #e5e7eb !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Sidebar text */
    .css-1d391kg, .css-1d391kg p, .css-1d391kg label {
        color: #e5e7eb;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #e5e7eb;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2D83C5;
    }
    
    /* Ensure all text is light for dark background */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown ul, .stMarkdown ol {
        color: #e5e7eb !important;
    }
    
    /* Text input and textarea styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        color: #ffffff !important;
        background-color: #2d2d2d !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > select {
        color: #ffffff !important;
        background-color: #2d2d2d !important;
    }
    
    /* Expander content */
    .streamlit-expanderContent {
        background-color: #1a1a1a !important;
        color: #e5e7eb !important;
        line-height: 1.6 !important;
        overflow: visible !important;
        clear: both !important;
    }

    /* Force proper text rendering and prevent overlap in all Streamlit containers */
    .streamlit-expanderContent > *,
    .stExpander > div > *,
    [data-testid="stExpanderDetails"] > * {
        line-height: 1.6 !important;
        margin-bottom: 0.75rem !important;
        display: block !important;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow: visible !important;
    }
    
    /* All Streamlit text elements */
    .element-container, .stText, .stMarkdownContainer {
        color: #e5e7eb !important;
    }
    
    /* Text within boxes/containers */
    .stTextArea textarea,
    .stTextInput input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
        color: #ffffff !important;
    }
    
    /* Expander content */
    .streamlit-expanderContent * {
        color: #e5e7eb !important;
    }
    
    /* Form submit buttons - use gradient */
    .stFormSubmitButton > button,
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #2D83C5 0%, #010066 100%) !important;
        color: white !important;
    }
    
    .stFormSubmitButton > button:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #010066 0%, #2D83C5 100%) !important;
        color: white !important;
    }
    
    /* Remove Streamlit default styling */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


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
    # Local development bypass - skip authentication
    if is_local_environment():
        # Auto-login as a local dev user
        if "user" not in st.session_state:
            st.session_state["user"] = {
                "email": "local@dev.local",
                "name": "Local Developer",
                "uid": "local-dev-user",
                "auth_method": "local",
                "email_verified": True
            }
    else:
        # Production/Replit: Handle Firebase ID token from external login page
        id_token = st.query_params.get("id_token")
        if id_token and "user" not in st.session_state:
            # Verify the token with Firebase Admin SDK
            try:
                firebase_auth.initialize_firebase_admin()
                if firebase_auth.is_firebase_admin_available():
                    from firebase_admin import auth as fb_auth
                    decoded = fb_auth.verify_id_token(id_token)
                    
                    # Store user in session state
                    st.session_state["user"] = {
                        "email": decoded.get("email"),
                        "name": decoded.get("name", decoded.get("email", "").split("@")[0]),
                        "uid": decoded.get("uid"),
                        "auth_method": "google" if decoded.get("firebase", {}).get("sign_in_provider") == "google.com" else "email",
                        "id_token": id_token,
                        "email_verified": decoded.get("email_verified", False)
                    }
                    
                    # Clean URL by removing id_token parameter
                    st.query_params.pop("id_token", None)
                    st.success(f"Welcome, {st.session_state['user']['name']}!")
                    st.rerun()
                else:
                    st.error("Firebase Admin SDK not initialized. Cannot verify token.")
            except Exception as e:
                st.error(f"Failed to verify token: {str(e)}")
                st.query_params.pop("id_token", None)
        
        # Check authentication (only in production)
        if not auth.is_authenticated():
            # Redirect to external login page
            login_page_url = os.getenv("FIREBASE_LOGIN_PAGE_URL", "https://vapi-assistant-builder-login.replit.app")
            return_to = os.getenv("STREAMLIT_APP_URL", "https://vapi-assistant-builder.replit.app")
            
            from urllib.parse import quote
            login_url = f"{login_page_url}?return_to={quote(return_to, safe='')}"
            
            # Styled authentication page matching login page design
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
            st.stop()
            return
    
    # Add logo and header
    st.markdown("""
    <div class="main-header">
        <div class="logo-container">
            <img src="data:image/png;base64,{}" class="logo-img" alt="skit.ai logo" />
        </div>
    </div>
    """.format(_get_logo_base64()), unsafe_allow_html=True)
    
    st.markdown("## VAPI Assistant Manager")
    st.markdown("Manage your voice assistant configurations")
    
    # Render logout button in sidebar
    auth_ui.render_logout_button()
    
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
    
    # Assistant selector - filter to only show assistants with "API" in the name
    assistants = st.session_state[ASSISTANTS_STORAGE_KEY]
    if not assistants:
        st.warning("No assistants found. Make sure your API key is correct.")
        st.stop()
    
    # Filter assistants to only include those with "API" in the name (case-insensitive)
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
    
    # Get current selected assistant ID
    current_assistant = st.session_state.get(SELECTED_ASSISTANT_STORAGE_KEY)
    current_id = current_assistant.get('id') if current_assistant else None
    
    # Find the default option based on current selection
    default_index = 0
    if current_id:
        for idx, (name, asst_id) in enumerate(assistant_options.items()):
            if asst_id == current_id:
                default_index = idx
                break
    
    selected_name = st.selectbox(
        "Select Assistant",
        options=list(assistant_options.keys()),
        index=default_index,
        key="assistant_selector"
    )
    
    selected_id = assistant_options[selected_name]
    
    # Load assistant data when selection changes
    if (current_assistant is None or current_assistant.get('id') != selected_id):
        with st.spinner("Loading assistant configuration..."):
            load_assistant_data(selected_id)
            st.rerun()  # Refresh the page to show the loaded assistant
    
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
    
    # Show existing FAQ context (always visible, before FAQs)
    # Note: Flows are extracted and passed to OpenAI but not shown in UI
    st.markdown("---")
    existing_prompt = st.session_state.get(SYSTEM_PROMPT_STORAGE_KEY, "")
    from utils.prompt_parser import extract_flows, extract_existing_faq_section, count_existing_faqs
    
    with st.expander("📋 View Existing FAQ Context", expanded=True):
        if existing_prompt:
            # Extract flows for OpenAI (not shown in UI)
            available_flows = extract_flows(existing_prompt)
            existing_faqs = extract_existing_faq_section(existing_prompt)
            existing_faq_count = count_existing_faqs(existing_prompt)
            
            if existing_faqs:
                st.markdown(f"**Existing FAQ Section:** ({existing_faq_count} FAQ{'s' if existing_faq_count != 1 else ''} found)")
                st.text_area(
                    "Existing FAQs",
                    value=existing_faqs,
                    height=150,
                    key="existing_faqs_display",
                    disabled=True,
                    help=f"These {existing_faq_count} FAQ(s) already exist in the prompt. Your new FAQs will be appended and numbered starting from {existing_faq_count + 1}."
                )
            else:
                st.info("No existing FAQ section found. This will be the first FAQ section.")
        else:
            st.warning("⚠️ No assistant loaded. Please select an assistant from the sidebar to see existing FAQs.")
            st.info("💡 Once you load an assistant, this section will show existing FAQ sections (if any).")
    
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
            
            if st.button("🤖 Generate FAQ Prompt", type="primary", use_container_width=True, key="generate_faq_prompt_inline"):
                if not faqs:
                    st.error("Please add at least one FAQ before generating the prompt.")
                else:
                    try:
                        with st.spinner("Generating FAQ prompt..."):
                            generated_prompt = faq_generator.generate_faqs(
                                faqs=faqs,
                                existing_prompt=existing_prompt if existing_prompt else None
                            )
                            st.session_state[FAQ_PROMPT_STORAGE_KEY] = generated_prompt
                            st.success("FAQ prompt generated successfully!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error generating FAQ prompt: {str(e)}")
            
            # Display generated FAQ prompt
            if st.session_state[FAQ_PROMPT_STORAGE_KEY]:
                st.markdown("---")
                # Header with regenerate button
                col_header1, col_header2 = st.columns([3, 1])
                with col_header1:
                    st.subheader("Generated FAQ Prompt")
                with col_header2:
                    if st.button("🔄 Regenerate", key="regenerate_faq_prompt", use_container_width=True):
                        # Regenerate using RAG (will retrieve different examples)
                        try:
                            with st.spinner("Regenerating FAQ prompt..."):
                                generated_prompt = faq_generator.generate_faqs(
                                    faqs=faqs,
                                    existing_prompt=existing_prompt if existing_prompt else None
                                )
                                st.session_state[FAQ_PROMPT_STORAGE_KEY] = generated_prompt
                                st.success("FAQ prompt regenerated successfully!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error regenerating FAQ prompt: {str(e)}")
                
                st.text_area(
                    "Generated Prompt",
                    value=st.session_state[FAQ_PROMPT_STORAGE_KEY],
                    height=200,
                    key="generated_faq_prompt_display_inline",
                    help="This prompt will be appended to the system prompt when you create the assistant."
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
                        
                        # Store the created assistant name for display
                        created_name = assistant_name.strip()
                        st.session_state["last_created_assistant_name"] = created_name
                        
                        # Display success message with assistant name and call button
                        st.success(f"✅ Assistant '{created_name}' created successfully!")
                        
                        # Display assistant name and call button in a styled container
                        st.markdown("---")
                        st.markdown("### 🎉 Assistant Created")
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"**Assistant Name:** `{created_name}`")
                        with col2:
                            call_url = "https://llm-studio.skit.ai/experience-assistant?region=us"
                            st.link_button("📞 Call Agent", call_url, use_container_width=True)
                        
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
