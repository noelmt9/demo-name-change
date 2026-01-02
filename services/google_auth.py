"""Google OAuth authentication service."""

import os
import streamlit as st
from typing import Optional, Dict
import requests

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

# OAuth scopes
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']


def get_google_auth_url() -> Optional[str]:
    """Get Google OAuth authorization URL."""
    if not GOOGLE_CLIENT_ID:
        return None
    
    # Build authorization URL manually (simpler for Streamlit)
    redirect_uri = GOOGLE_REDIRECT_URI or "http://localhost:8501"
    
    # Generate state
    import secrets
    import string
    state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    st.session_state["oauth_state"] = state
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent"
    }
    
    from urllib.parse import urlencode
    auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)
    return auth_url


def handle_google_callback(code: str, state: str) -> Optional[Dict]:
    """
    Handle Google OAuth callback and get user info.
    
    Returns:
        user_info: Dict with email, name, google_id
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return None
    
    # Verify state
    if state != st.session_state.get("oauth_state"):
        st.warning("Invalid state parameter. Please try logging in again.")
        return None
    
    try:
        redirect_uri = GOOGLE_REDIRECT_URI or "http://localhost:8501"
        
        # Exchange code for token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            st.error(f"Failed to get access token: {token_response.text}")
            return None
        
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            st.error("No access token received from Google")
            return None
        
        # Get user info from Google
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if user_info_response.status_code == 200:
            user_data = user_info_response.json()
            return {
                "email": user_data.get("email"),
                "name": user_data.get("name", user_data.get("email", "").split('@')[0]),
                "google_id": user_data.get("id"),
                "picture": user_data.get("picture")
            }
        else:
            st.error(f"Failed to get user info: {user_info_response.text}")
            return None
    except Exception as e:
        st.error(f"Error during Google authentication: {str(e)}")
        return None


def is_google_configured() -> bool:
    """Check if Google OAuth is configured."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

