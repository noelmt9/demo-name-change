"""Authentication UI components for Streamlit."""

import json
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
    """Render Google Sign-In via Firebase Web SDK (no separate Google OAuth env vars)."""
    if not firebase_auth.is_firebase_configured():
        return

    st.markdown("---")
    st.markdown("**Or continue with:**")

    # We can sign in without Admin SDK, but we can't *verify* the token server-side without it.
    if not firebase_auth.is_firebase_admin_available():
        st.info(
            "**Google Sign-In requires Firebase Admin SDK credentials:**\n\n"
            "**For Local:** Set `FIREBASE_CREDENTIALS_PATH=data/firebase-service-account.json` in `.env`\n\n"
            "**For Replit:** Add `FIREBASE_SERVICE_ACCOUNT_JSON` as a Secret with the full JSON content"
        )
        return

    config = firebase_auth.get_firebase_config()
    # Firebase JS only needs these keys; keep payload minimal.
    js_config = {
        "apiKey": config.get("apiKey", ""),
        "authDomain": config.get("authDomain", ""),
        "projectId": config.get("projectId", ""),
        "appId": config.get("appId", ""),
    }

    html = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body style="margin:0;padding:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
    <button id="googleBtn" style="
      width: 100%;
      background: #4285F4;
      color: #fff;
      border: 0;
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 16px;
      cursor: pointer;">
      Continue with Google
    </button>
    <div id="status" style="margin-top:8px;font-size:12px;color:#666;line-height:1.35;"></div>

    <script type="module">
      import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
      import {{ getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

      const firebaseConfig = {json.dumps(js_config)};
      const app = initializeApp(firebaseConfig);
      const auth = getAuth(app);
      const provider = new GoogleAuthProvider();

      const btn = document.getElementById("googleBtn");
      const statusEl = document.getElementById("status");

      function setStatus(text, isError = false) {{
        statusEl.textContent = text || "";
        statusEl.style.color = isError ? "#b00020" : "#666";
      }}

      async function finishWithIdToken(user) {{
        const token = await user.getIdToken();
        const url = new URL(window.location.href);
        url.searchParams.set("firebase_id_token", token);
        window.location.href = url.toString();
      }}

      // If we returned from a redirect-based sign-in, complete it here.
      try {{
        const redirectResult = await getRedirectResult(auth);
        if (redirectResult && redirectResult.user) {{
          setStatus("Finishing Google sign-in…");
          await finishWithIdToken(redirectResult.user);
        }}
      }} catch (e) {{
        const code = e?.code ? String(e.code) : "";
        const msg = e?.message ? String(e.message) : String(e);
        setStatus(`Google redirect failed: ${{code}} ${{msg}}`, true);
        console.error(e);
      }}

      btn.addEventListener("click", async () => {{
        try {{
          setStatus("");
          btn.disabled = true;
          btn.innerText = "Opening Google…";
          const result = await signInWithPopup(auth, provider);
          const user = result.user;
          await finishWithIdToken(user);
        }} catch (e) {{
          const code = e?.code ? String(e.code) : "";
          const msg = e?.message ? String(e.message) : String(e);
          console.error(e);

          // Common on hosted/embedded UIs: popup blocked or unsupported → fall back to redirect.
          if (code === "auth/popup-blocked" || code === "auth/operation-not-supported-in-this-environment") {{
            setStatus(`Popup blocked (${{
              code
            }}). Redirecting to Google…`);
            btn.innerText = "Redirecting…";
            await signInWithRedirect(auth, provider);
            return;
          }}

          btn.innerText = "Google Sign-In failed — try again";
          btn.disabled = false;
          setStatus(`Google sign-in failed: ${{code}} ${{msg}}`, true);
        }}
      }});
    </script>
  </body>
</html>
"""
    components.html(html, height=60)


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
