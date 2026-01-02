"""Authentication service - Firebase wrapper for backward compatibility."""

import streamlit as st
from typing import Optional, Dict
from services import firebase_auth

# Re-export Firebase auth functions for backward compatibility
get_current_user = firebase_auth.get_current_user
is_authenticated = firebase_auth.is_authenticated
logout = firebase_auth.logout


# Wrapper functions for Firebase auth
def register_user(email: str, password: str, name: str = "") -> tuple[bool, str]:
    """
    Register a new user with email and password using Firebase.
    
    Returns:
        (success: bool, message: str)
    """
    success, message, user_data = firebase_auth.register_user_email_password(email, password, name)
    if success and user_data:
        st.session_state["user"] = user_data
    return success, message


def login_user(email: str, password: str) -> tuple[bool, str, Optional[Dict]]:
    """
    Login a user with email and password using Firebase.
    
    Returns:
        (success: bool, message: str, user_data: Optional[Dict])
    """
    return firebase_auth.login_user_email_password(email, password)
