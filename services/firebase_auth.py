"""Firebase Authentication service."""

import os
import json
import streamlit as st
from typing import Optional, Dict
import pyrebase
import firebase_admin
from firebase_admin import credentials, auth

# Firebase configuration from environment variables
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")
FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "")
FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID", "")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "")

# Firebase Admin SDK credentials (optional, for server-side operations)
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")

# Initialize Firebase Admin SDK (if credentials provided)
_firebase_admin_initialized = False


def initialize_firebase_admin():
    """Initialize Firebase Admin SDK."""
    global _firebase_admin_initialized
    
    # Check if already initialized
    if _firebase_admin_initialized:
        return
    
    # Check if Firebase Admin app already exists (from a previous failed attempt)
    try:
        # Try to get the default app - if it exists, we're already initialized
        firebase_admin.get_app()
        _firebase_admin_initialized = True
        return
    except ValueError:
        # App doesn't exist yet, proceed with initialization
        pass

    # 1) Preferred for Replit/hosted: JSON stored in env var/secret
    if FIREBASE_SERVICE_ACCOUNT_JSON:
        try:
            # Handle both string JSON and already-parsed dict
            if isinstance(FIREBASE_SERVICE_ACCOUNT_JSON, str):
                service_account_info = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
            else:
                service_account_info = FIREBASE_SERVICE_ACCOUNT_JSON
            
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            _firebase_admin_initialized = True
            return
        except ValueError as e:
            # App already exists - mark as initialized
            if "already exists" in str(e):
                _firebase_admin_initialized = True
                return
            st.error(f"❌ Failed to initialize Firebase Admin: {str(e)}")
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {str(e)}")
            st.info("💡 Make sure you pasted the **entire JSON content** as the secret value, not just a path.")
        except Exception as e:
            st.error(f"❌ Failed to initialize Firebase Admin from FIREBASE_SERVICE_ACCOUNT_JSON: {str(e)}")

    # 2) Local dev: JSON file path
    if FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
        try:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            _firebase_admin_initialized = True
            return
        except ValueError as e:
            # App already exists - mark as initialized
            if "already exists" in str(e):
                _firebase_admin_initialized = True
                return
            st.error(f"❌ Failed to initialize Firebase Admin: {str(e)}")
        except Exception as e:
            st.error(f"❌ Failed to initialize Firebase Admin from FIREBASE_CREDENTIALS_PATH: {str(e)}")

    # 3) Fallback: default credentials (may work on some cloud runtimes)
    try:
        firebase_admin.initialize_app()
        _firebase_admin_initialized = True
    except ValueError as e:
        # App already exists - mark as initialized
        if "already exists" in str(e):
            _firebase_admin_initialized = True
        # Otherwise, silently fail - Admin SDK not required for email/password
    except Exception:
        pass  # Admin SDK not required for email/password; only needed to verify Google ID tokens


def is_firebase_admin_available() -> bool:
    """
    Returns True if Firebase Admin SDK is initialized and available for secure token verification.
    """
    initialize_firebase_admin()
    return bool(_firebase_admin_initialized)


def get_firebase_config() -> Dict:
    """Get Firebase configuration dictionary."""
    return {
        "apiKey": FIREBASE_API_KEY,
        "authDomain": FIREBASE_AUTH_DOMAIN,
        "projectId": FIREBASE_PROJECT_ID,
        "storageBucket": FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": FIREBASE_MESSAGING_SENDER_ID,
        "appId": FIREBASE_APP_ID,
        "databaseURL": FIREBASE_DATABASE_URL
    }


def get_firebase_app():
    """Get or create Firebase app instance."""
    config = get_firebase_config()
    
    # Check if all required config is present
    if not all([config["apiKey"], config["authDomain"], config["projectId"]]):
        return None
    
    try:
        firebase = pyrebase.initialize_app(config)
        return firebase
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {str(e)}")
        return None


def is_firebase_configured() -> bool:
    """Check if Firebase is properly configured."""
    config = get_firebase_config()
    return bool(config["apiKey"] and config["authDomain"] and config["projectId"])


def register_user_email_password(email: str, password: str, name: str = "") -> tuple[bool, str, Optional[Dict]]:
    """
    Register a new user with email and password using Firebase.
    
    Returns:
        (success: bool, message: str, user_data: Optional[Dict])
    """
    if not is_firebase_configured():
        return False, "Firebase is not configured. Please set Firebase environment variables.", None
    
    firebase = get_firebase_app()
    if not firebase:
        return False, "Failed to initialize Firebase.", None
    
    try:
        auth_instance = firebase.auth()
        
        # Create user
        user = auth_instance.create_user_with_email_and_password(email, password)
        
        # Update user profile with name if provided
        if name:
            try:
                auth_instance.update_profile(user['idToken'], display_name=name)
            except:
                pass  # Name update is optional
        
        # Get user data
        user_data = {
            "email": email,
            "name": name or email.split('@')[0],
            "uid": user['localId'],
            "auth_method": "email",
            "id_token": user['idToken'],
            "refresh_token": user['refreshToken']
        }
        
        return True, "Registration successful!", user_data
        
    except Exception as e:
        error_msg = str(e)
        if "EMAIL_EXISTS" in error_msg:
            return False, "Email already registered. Please login instead.", None
        elif "WEAK_PASSWORD" in error_msg:
            return False, "Password is too weak. Please use a stronger password.", None
        else:
            return False, f"Registration failed: {error_msg}", None


def login_user_email_password(email: str, password: str) -> tuple[bool, str, Optional[Dict]]:
    """
    Login a user with email and password using Firebase.
    
    Returns:
        (success: bool, message: str, user_data: Optional[Dict])
    """
    if not is_firebase_configured():
        return False, "Firebase is not configured. Please set Firebase environment variables.", None
    
    firebase = get_firebase_app()
    if not firebase:
        return False, "Failed to initialize Firebase.", None
    
    try:
        auth_instance = firebase.auth()
        
        # Sign in user
        user = auth_instance.sign_in_with_email_and_password(email, password)
        
        # Get user info
        user_info = auth_instance.get_account_info(user['idToken'])
        
        if user_info and 'users' in user_info and len(user_info['users']) > 0:
            user_data_firebase = user_info['users'][0]
            user_data = {
                "email": user_data_firebase.get('email', email),
                "name": user_data_firebase.get('displayName', email.split('@')[0]),
                "uid": user_data_firebase.get('localId', user['localId']),
                "auth_method": "email",
                "id_token": user['idToken'],
                "refresh_token": user['refreshToken'],
                "email_verified": user_data_firebase.get('emailVerified', False)
            }
            return True, "Login successful!", user_data
        else:
            return False, "Failed to get user information.", None
            
    except Exception as e:
        error_msg = str(e)
        if "INVALID_PASSWORD" in error_msg or "EMAIL_NOT_FOUND" in error_msg:
            return False, "Invalid email or password.", None
        else:
            return False, f"Login failed: {error_msg}", None


def get_google_auth_url() -> Optional[str]:
    """Get Google OAuth URL for Firebase Auth."""
    if not is_firebase_configured():
        return None
    
    # For Firebase, we need to use Google OAuth with Firebase as the provider
    # This requires setting up OAuth 2.0 credentials in Google Cloud Console
    # For now, we'll use a token-based approach
    return None


def sign_in_with_google_id_token(id_token: str) -> tuple[bool, str, Optional[Dict]]:
    """
    Sign in with Google using a Firebase ID token.
    The ID token should be obtained from Firebase client SDK after Google OAuth.
    
    Returns:
        (success: bool, message: str, user_data: Optional[Dict])
    """
    if not is_firebase_configured():
        return False, "Firebase is not configured.", None
    
    # Verify the ID token
    user_data = verify_id_token(id_token)
    if user_data:
        return True, "Google sign-in successful!", user_data
    else:
        return False, "Invalid or expired token.", None


def create_or_get_firebase_user_from_google(email: str, name: str, google_id: str) -> Optional[Dict]:
    """
    Create or get Firebase user from Google OAuth info.
    Uses Firebase Admin SDK to create user if needed.
    
    Returns:
        user_data: Dict with Firebase user info
    """
    initialize_firebase_admin()
    
    if not _firebase_admin_initialized:
        # Fallback: return basic user info without Firebase token
        return {
            "email": email,
            "name": name,
            "auth_method": "google",
            "google_id": google_id
        }
    
    try:
        # Check if user exists
        try:
            user = auth.get_user_by_email(email)
            uid = user.uid
        except:
            # User doesn't exist, create them
            user = auth.create_user(
                email=email,
                display_name=name,
                email_verified=True
            )
            uid = user.uid
        
        # Create custom token and sign in
        custom_token = auth.create_custom_token(uid)
        custom_token_str = custom_token.decode('utf-8')
        
        # Sign in with custom token using Pyrebase
        firebase = get_firebase_app()
        if firebase:
            auth_instance = firebase.auth()
            user_cred = auth_instance.sign_in_with_custom_token(custom_token_str)
            
            return {
                "email": email,
                "name": name,
                "uid": uid,
                "auth_method": "google",
                "id_token": user_cred.get("idToken"),
                "refresh_token": user_cred.get("refreshToken"),
                "google_id": google_id
            }
        
        # Fallback if Pyrebase sign-in fails
        return {
            "email": email,
            "name": name,
            "uid": uid,
            "auth_method": "google",
            "google_id": google_id
        }
    except Exception as e:
        st.error(f"Failed to create Firebase user: {str(e)}")
        # Fallback: return basic info
        return {
            "email": email,
            "name": name,
            "auth_method": "google",
            "google_id": google_id
        }


def verify_id_token(id_token: str) -> Optional[Dict]:
    """
    Verify a Firebase ID token using Admin SDK.

    Returns:
        user_data: Dict or None if invalid
    """
    initialize_firebase_admin()

    if not _firebase_admin_initialized:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            "uid": decoded_token.get('uid'),
            "email": decoded_token.get('email'),
            "name": decoded_token.get('name', decoded_token.get('email', '').split('@')[0]),
            "email_verified": decoded_token.get('email_verified', False)
        }
    except Exception:
        return None


def refresh_user_token(refresh_token: str) -> Optional[Dict]:
    """
    Refresh a Firebase ID token using a refresh token.

    Returns:
        user_data: Dict with new tokens or None if refresh failed
    """
    if not is_firebase_configured():
        return None

    firebase = get_firebase_app()
    if not firebase:
        return None

    try:
        auth_instance = firebase.auth()

        # Refresh the ID token
        user = auth_instance.refresh(refresh_token)

        # Get updated user info
        user_info = auth_instance.get_account_info(user['idToken'])

        if user_info and 'users' in user_info and len(user_info['users']) > 0:
            user_data_firebase = user_info['users'][0]
            return {
                "email": user_data_firebase.get('email'),
                "name": user_data_firebase.get('displayName', user_data_firebase.get('email', '').split('@')[0]),
                "uid": user_data_firebase.get('localId'),
                "id_token": user['idToken'],
                "refresh_token": user.get('refreshToken', refresh_token),
                "email_verified": user_data_firebase.get('emailVerified', False)
            }

        return None
    except Exception as e:
        # Refresh failed
        return None


def get_current_user() -> Optional[Dict]:
    """Get the currently logged-in user from session state."""
    return st.session_state.get("user")


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    user = get_current_user()
    # Simply check if user exists in session state
    # Token verification and refresh happens during handle_authentication()
    # Not on every single function call
    return user is not None


def logout():
    """Logout the current user."""
    if "user" in st.session_state:
        del st.session_state["user"]

    # Clear localStorage
    from streamlit.components.v1 import html
    html("""
    <script>
        localStorage.removeItem('firebase_refresh_token');
    </script>
    """, height=0)

