"""Authentication UI components for Streamlit."""

import json
import os
from pathlib import Path
from urllib.parse import urlencode
import streamlit as st
import streamlit.components.v1 as components

from services import auth
from services import firebase_auth


def render_login_page():
    """Render the login/registration page."""
    st.title("🔐 Authentication Required")
    st.markdown("Please login or register to access the VAPI Assistant Manager")

    # Handle Firebase Google Sign-In callback (ID token returned via query params)
    id_token = _get_query_param("firebase_id_token")
    if id_token:
        if not firebase_auth.is_firebase_admin_available():
            st.error(
                "Google Sign-In requires Firebase Admin SDK credentials to verify tokens. "
                "Set `FIREBASE_CREDENTIALS_PATH` to your service account JSON (and restart the app)."
            )
            _clear_query_param("firebase_id_token")
            return

        verified = firebase_auth.verify_id_token(id_token)
        if verified:
            st.session_state["user"] = {
                "email": verified.get("email"),
                "name": verified.get("name"),
                "uid": verified.get("uid"),
                "auth_method": "google",
                "id_token": id_token,
            }
            _clear_query_param("firebase_id_token")
            st.success(f"Welcome, {st.session_state['user']['name']}!")
            st.rerun()
        else:
            st.error("Google Sign-In failed: invalid or expired token. Please try again.")
            _clear_query_param("firebase_id_token")
            return
    
    # Default to Register tab, allow switching to Login
    default_tab = st.session_state.get("auth_tab", "register")
    
    # Tabs for Register (default) and Login
    tab1, tab2 = st.tabs(["📝 Register", "🔑 Login"])
    
    if default_tab == "login":
        # Show login first if user clicked "Already have an account"
        with tab2:
            render_login_form()
        with tab1:
            render_register_form()
    else:
        # Default: Show register first
        with tab1:
            render_register_form()
        with tab2:
            render_login_form()


def render_login_form():
    """Render the login form."""
    st.subheader("Sign In")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        login_button = st.form_submit_button("Sign In", use_container_width=True, type="primary")
        
        if login_button:
            if email and password:
                success, message, user_data = auth.login_user(email, password)
                if success and user_data:
                    st.session_state["user"] = user_data
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter both email and password")
    
    _render_google_sign_in()
    
    # Switch to register
    st.markdown("---")
    if st.button("Don't have an account? Register", use_container_width=True, key="switch_to_register"):
        st.session_state["auth_tab"] = "register"
        st.rerun()


def render_register_form():
    """Render the registration form."""
    st.subheader("Create New Account")
    
    with st.form("register_form"):
        name = st.text_input("Name (Optional)", placeholder="Your name")
        email = st.text_input("Email *", placeholder="your.email@example.com")
        password = st.text_input("Password *", type="password", placeholder="At least 6 characters")
        password_confirm = st.text_input("Confirm Password *", type="password", placeholder="Re-enter password")
        
        register_button = st.form_submit_button("Register", use_container_width=True, type="primary")
        
        if register_button:
            if not email or not password:
                st.error("Email and password are required")
            elif password != password_confirm:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                success, message = auth.register_user(email, password, name)
                if success:
                    st.success(message)
                    # User is already logged in after registration
                    st.rerun()
                else:
                    st.error(message)
    
    _render_google_sign_in()
    
    # Switch to login
    st.markdown("---")
    if st.button("Already have an account? Sign in", use_container_width=True, key="switch_to_login"):
        st.session_state["auth_tab"] = "login"
        st.rerun()

def _render_google_sign_in():
    """Render Google Sign-In link to external login page."""
    if not firebase_auth.is_firebase_configured():
        return

    st.markdown("---")
    st.markdown("**Or continue with:**")

    # Get the login page URL from environment or use default
    login_page_url = os.getenv("FIREBASE_LOGIN_PAGE_URL", "https://vapi-login.replit.app")
    
    # Get the current Streamlit app URL for return redirect
    # For Replit, construct from known info
    try:
        # Try to get from environment (set in Replit)
        return_to = os.getenv("STREAMLIT_APP_URL", "")
        if not return_to:
            # Fallback: construct from current request (may not work in all cases)
            # For Replit, you should set STREAMLIT_APP_URL env var
            return_to = "https://vapi-assistant-builder.replit.app"  # Update with your actual Replit URL
    except:
        return_to = "https://vapi-assistant-builder.replit.app"  # Update with your actual Replit URL
    
    # Build the login URL with return_to parameter
    from urllib.parse import quote
    login_url = f"{login_page_url}?return_to={quote(return_to, safe='')}"
    
    # Show a button/link that navigates to the login page
    st.markdown(
        f'<a href="{login_url}" style="text-decoration: none;">'
        f'<button style="width: 100%; background: #4285F4; color: #fff; border: 0; border-radius: 8px; padding: 12px 14px; font-size: 16px; cursor: pointer;">'
        f'🔵 Continue with Google'
        f'</button></a>',
        unsafe_allow_html=True
    )


def _build_inline_auth_url(config: dict, return_url: str = "") -> str:
    """Build HTML content for Firebase auth (will be used in blob URL to allow storage access)."""
    # Read the HTML template
    html_path = Path(__file__).parent.parent / "static" / "firebase_auth.html"
    
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        # Fallback: minimal inline HTML
        html_content = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Google Sign-In</title></head>
<body><div style="text-align:center;padding:2rem;"><p>Signing in with Google...</p></div>
<script type="module">
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithRedirect, getRedirectResult } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
const urlParams = new URLSearchParams(window.location.search);
const firebaseConfig = {
    apiKey: urlParams.get('apiKey'),
    authDomain: urlParams.get('authDomain'),
    projectId: urlParams.get('projectId'),
    appId: urlParams.get('appId')
};
const returnUrl = urlParams.get('returnUrl') || window.location.origin;
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
(async function() {
    try {
        const result = await getRedirectResult(auth);
        if (result && result.user) {
            const token = await result.user.getIdToken();
            const url = new URL(returnUrl || window.location.origin);
            url.searchParams.set('firebase_id_token', token);
            window.location.href = url.toString();
        } else {
            await signInWithRedirect(auth, provider);
        }
    } catch (error) {
        document.body.innerHTML = '<div style="text-align:center;padding:2rem;"><p style="color:red;">Error: ' + (error.message || error.code) + '</p></div>';
    }
})();
</script>
</body></html>"""
    
    # Directly inject the config values into the HTML
    api_key = config.get("apiKey", "")
    auth_domain = config.get("authDomain", "")
    project_id = config.get("projectId", "")
    app_id = config.get("appId", "")
    return_url_value = return_url if return_url else ""
    
    # Replace urlParams.get() calls with actual values
    html_with_config = html_content
    html_with_config = html_with_config.replace("urlParams.get('apiKey')", json.dumps(api_key))
    html_with_config = html_with_config.replace("urlParams.get('authDomain')", json.dumps(auth_domain))
    html_with_config = html_with_config.replace("urlParams.get('projectId')", json.dumps(project_id))
    html_with_config = html_with_config.replace("urlParams.get('appId')", json.dumps(app_id))
    if return_url_value:
        html_with_config = html_with_config.replace("urlParams.get('returnUrl') || window.location.origin", json.dumps(return_url_value))
    else:
        html_with_config = html_with_config.replace("urlParams.get('returnUrl') || window.location.origin", "window.location.origin")
    
    # Return the HTML content (will be converted to blob URL in the calling function)
    return html_with_config


def _get_query_param(key: str) -> str | None:
    try:
        val = st.query_params.get(key)
        if isinstance(val, list):
            return val[0] if val else None
        return val
    except Exception:
        return None


def _clear_query_param(key: str) -> None:
    try:
        st.query_params.pop(key, None)
    except Exception:
        # Fallback for older Streamlit versions
        try:
            st.query_params.clear()
        except Exception:
            pass


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
