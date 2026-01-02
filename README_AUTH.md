# Authentication Setup Guide

This application now includes user authentication with two methods:
1. **Email/Password Registration & Login**
2. **Google OAuth Login**

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Google OAuth (Optional)

To enable Google login, you need to:

1. **Create a Google OAuth Application:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable Google+ API
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - For local: `http://localhost:8501`
     - For production: `https://your-domain.com`

2. **Set Environment Variables:**
   ```bash
   # Add to your .env file
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8501  # or your production URL
   ```

### 3. User Database

- User data is stored in `data/users.json` (automatically created)
- This file is in `.gitignore` and will not be committed
- Passwords are hashed using bcrypt

## Usage

### Registration

1. Click on the "Register" tab
2. Enter your email and password (minimum 8 characters)
3. Optionally enter your name
4. Click "Register"
5. You'll be automatically logged in after registration

### Login

1. Click on the "Login" tab
2. Enter your email and password
3. Click "Login"

### Google Login

1. Click "Login with Google" or "Register with Google"
2. You'll be redirected to Google's authorization page
3. After authorization, copy the authorization code from the URL
4. Paste it in the "Authorization Code" field
5. Click "Verify Code"

**Note:** For production, you may want to set up proper OAuth redirect handling.

## Security Features

- ✅ Passwords are hashed using bcrypt
- ✅ User database is not committed to git
- ✅ Session-based authentication
- ✅ Support for both email and Google authentication

## File Structure

```
services/
  ├── auth.py              # Email/password authentication
  └── google_auth.py       # Google OAuth authentication

components/
  └── auth_ui.py          # Authentication UI components

data/
  └── users.json          # User database (auto-created, git-ignored)
```

## Troubleshooting

### Google OAuth Not Working

- Make sure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in your `.env` file
- Verify the redirect URI matches what you configured in Google Cloud Console
- Check that Google+ API is enabled in your Google Cloud project

### Can't Login After Registration

- Make sure the `data/` directory exists and is writable
- Check that passwords are at least 8 characters long
- Verify the user database file was created: `data/users.json`

