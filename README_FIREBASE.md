# Firebase Authentication Setup Guide

This application uses **Firebase Authentication** instead of Google Cloud Console for user management.

## Why Firebase?

- ✅ Built-in email/password authentication
- ✅ Google Sign-In integration
- ✅ Secure token-based authentication
- ✅ User management dashboard
- ✅ Better suited for web applications
- ✅ No need for manual OAuth flow handling

## Setup Instructions

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or select an existing project
3. Follow the setup wizard
4. Enable **Authentication** in the Firebase Console

### 2. Enable Authentication Methods

In Firebase Console → Authentication → Sign-in method:

1. **Enable Email/Password:**
   - Click "Email/Password"
   - Enable "Email/Password" (first toggle)
   - Click "Save"

2. **Enable Google Sign-In (Optional):**
   - Click "Google"
   - Enable it
   - Add your project's support email
   - Click "Save"

### 3. Get Firebase Configuration

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Scroll down to "Your apps"
3. Click the web icon (`</>`) to add a web app
4. Register your app (give it a name)
5. Copy the Firebase configuration object

### 4. Set Environment Variables

Add these to your `.env` file using your Firebase configuration:

```bash
# Firebase Configuration (from Firebase Console)
# Get these values from Firebase Console → Project Settings → Your apps → Web app config
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com  # Optional

# Firebase Admin SDK (Optional - for server-side operations)
# Download service account key from Firebase Console → Project Settings → Service Accounts
FIREBASE_CREDENTIALS_PATH=path/to/serviceAccountKey.json
```

### 5. Get Firebase Admin SDK Credentials (Optional)

For server-side token verification:

1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Generate new private key"
3. Download the JSON file
4. Save it securely (add to `.gitignore`)
5. Set `FIREBASE_CREDENTIALS_PATH` in your `.env` file

## Installation

```bash
pip install -r requirements.txt
```

## Features

### Email/Password Authentication

- ✅ User registration with email and password
- ✅ User login with email and password
- ✅ Password validation (minimum 6 characters)
- ✅ Automatic user creation in Firebase
- ✅ Secure token-based sessions

### Google Sign-In

- ✅ Enabled via the **Firebase Web SDK** (popup flow)
- ✅ No separate `GOOGLE_OAUTH_CLIENT_ID/SECRET` env vars needed in this app
- ✅ Requires **Firebase Admin SDK** credentials on the server to securely verify the returned Firebase ID token (`FIREBASE_CREDENTIALS_PATH`)

## How It Works

1. **Registration:**
   - User enters email and password
   - Firebase creates the user account
   - User is automatically logged in
   - User data stored in Firebase

2. **Login:**
   - User enters email and password
   - Firebase authenticates
   - Returns ID token and refresh token
   - Token stored in session state

3. **Session Management:**
   - ID token stored in Streamlit session state
   - Token can be verified using Firebase Admin SDK
   - Session persists until logout or expiration

## Security Features

- ✅ Passwords never stored (Firebase handles hashing)
- ✅ Secure token-based authentication
- ✅ Token expiration and refresh
- ✅ Email verification support (optional)
- ✅ Firebase security rules

## File Structure

```
services/
  ├── firebase_auth.py    # Firebase authentication service
  └── auth.py             # Wrapper for backward compatibility

components/
  └── auth_ui.py          # Authentication UI components
```

## Troubleshooting

### "Firebase is not configured"

- Make sure all Firebase environment variables are set in `.env`
- Check that `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, and `FIREBASE_PROJECT_ID` are present

### "Failed to initialize Firebase"

- Verify your Firebase configuration values are correct
- Check that Authentication is enabled in Firebase Console
- Ensure your Firebase project is active

### "Email already registered"

- The email is already in use in Firebase
- Try logging in instead of registering
- Or use a different email address

### "Password is too weak"

- Firebase requires minimum 6 characters
- Use a stronger password with letters, numbers, and special characters

## Migration from Google Cloud Console

If you were using Google Cloud Console OAuth before:

1. ✅ No code changes needed - Firebase handles it
2. ✅ Users need to re-register (or you can migrate them)
3. ✅ Firebase provides better user management
4. ✅ Simpler configuration

## Next Steps

- [ ] Enable email verification
- [ ] Add password reset functionality
- [ ] Implement Google Sign-In with proper redirect
- [ ] Add user profile management
- [ ] Set up Firebase security rules

