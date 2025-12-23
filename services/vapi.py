"""VAPI API service functions."""

import requests
import os
from typing import List, Dict, Optional

# Import config values - these will be read fresh each time the module is imported
# But we'll also check environment variables directly to avoid caching issues
VAPI_API_BASE_URL = "https://api.vapi.ai"


def get_api_key() -> Optional[str]:
    """
    Get VAPI API key from config or environment variable.
    Checks environment variable first (takes precedence), then falls back to config.
    This helps avoid Streamlit module caching issues.
    """
    # Check environment variable first (takes precedence)
    env_key = os.getenv("VAPI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    
    # Fall back to config import
    try:
        from config import VAPI_API_KEY as config_key
        key = config_key if config_key else None
        if key and key.strip():
            return key.strip()
    except ImportError:
        pass
    
    return None


def make_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> requests.Response:
    """
    Make authenticated request to VAPI API.
    
    Args:
        method: HTTP method (GET, PATCH, etc.)
        endpoint: API endpoint path (e.g., "/assistant")
        data: Optional request body data for PATCH/POST requests
        params: Optional query parameters for GET requests
    
    Returns:
        Response object from requests library
    
    Raises:
        ValueError: If API key is missing
        requests.exceptions.RequestException: If request fails
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("VAPI API key is required. Please set VAPI_API_KEY in config.py or as an environment variable.")
    
    # Strip whitespace in case there's accidental spacing
    api_key = api_key.strip()
    
    # Debug: Log first and last few characters of key (for debugging without exposing full key)
    import logging
    logging.debug(f"Using API key: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
    
    url = f"{VAPI_API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        # Provide more detailed error information
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.text
                # Try to parse JSON error if available
                try:
                    error_json = e.response.json()
                    if isinstance(error_json, dict) and 'message' in error_json:
                        error_detail = error_json['message']
                except:
                    pass
            except:
                error_detail = str(e)
            
            status_code = e.response.status_code
            if status_code == 401:
                error_msg = f"HTTP 401 Unauthorized: Invalid API key. Please verify your VAPI API key in config.py or get a valid private API key from https://dashboard.vapi.ai. Error details: {error_detail}"
            else:
                error_msg = f"HTTP {status_code}: {error_detail}"
        else:
            error_msg = f"HTTP Error: {str(e)}"
        raise requests.exceptions.RequestException(error_msg) from e
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Request failed: {str(e)}") from e


def list_assistants(limit: Optional[int] = 500) -> List[Dict]:
    """
    Fetch list of assistants from VAPI.
    
    According to VAPI API docs: GET https://api.vapi.ai/assistant
    Returns an array of Assistant objects.
    
    Args:
        limit: Optional maximum number of items to return (defaults to 500)
    
    Returns:
        List of assistant dictionaries
    
    Raises:
        Exception: If request fails or response is invalid
    """
    try:
        params = {}
        if limit is not None:
            params["limit"] = limit
        
        response = make_request("GET", "/assistant", params=params)
        assistants = response.json()
        
        # According to API docs, response is an array of Assistant objects
        if not isinstance(assistants, list):
            raise ValueError(f"Expected array response, got {type(assistants)}")
        
        return assistants
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to load assistants: {str(e)}")
    except (ValueError, KeyError) as e:
        raise Exception(f"Invalid response format: {str(e)}")


def get_assistant(assistant_id: str) -> Optional[Dict]:
    """
    Fetch assistant details from VAPI.
    
    Args:
        assistant_id: Unique identifier for the assistant
    
    Returns:
        Assistant dictionary or None if not found
    
    Raises:
        Exception: If request fails
    """
    try:
        response = make_request("GET", f"/assistant/{assistant_id}")
        assistant = response.json()
        return assistant
    except requests.exceptions.RequestException as e:
        # Check if it's a 404 error (assistant not found)
        error_str = str(e)
        if "404" in error_str or "Not Found" in error_str:
            return None
        raise Exception(f"Failed to load assistant: {str(e)}")


def update_assistant(assistant_id: str, updates: Dict) -> bool:
    """
    Update assistant configuration.
    
    Args:
        assistant_id: Unique identifier for the assistant
        updates: Dictionary containing fields to update
    
    Returns:
        True if update was successful
    
    Raises:
        Exception: If request fails
    """
    try:
        make_request("PATCH", f"/assistant/{assistant_id}", data=updates)
        return True
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to update assistant: {str(e)}")


def create_assistant(assistant_data: Dict) -> Dict:
    """
    Create a new assistant.
    
    Args:
        assistant_data: Dictionary containing assistant configuration
    
    Returns:
        Created assistant dictionary
    
    Raises:
        Exception: If request fails
    """
    try:
        response = make_request("POST", "/assistant", data=assistant_data)
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create assistant: {str(e)}")


