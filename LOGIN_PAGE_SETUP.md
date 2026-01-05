# Login Page Setup Guide

This guide will walk you through setting up a separate login page on Replit for Firebase Google Sign-In.

## Step 1: Create a New Replit Static Site

1. Go to [Replit](https://replit.com) and click **"Create Repl"**
2. Choose **"HTML, CSS, JS"** template (Static site)
3. Name it something like: `vapi-login` or `vapi-auth-page`
4. Click **"Create Repl"**
5. **Run it once** so it gets a URL like: `https://vapi-login.replit.app`
   - Note this URL - you'll need it later!

## Step 2: Add the Login Page HTML

1. In your new Replit, you'll see an `index.html` file
2. **Replace the entire contents** with the HTML code below
3. **IMPORTANT**: Update the `firebaseConfig` object with your Firebase web config values:

```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {
        font-family: system-ui, -apple-system, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
        background: #f5f5f5;
      }
      .container {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
      }
      h2 {
        margin-top: 0;
        color: #333;
      }
      button {
        background: #4285F4;
        color: #fff;
        border: 0;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 16px;
        cursor: pointer;
        font-weight: 500;
      }
      button:hover {
        background: #357ae8;
      }
      #msg {
        margin-top: 1rem;
        color: #b00020;
        font-size: 14px;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h2>Sign in</h2>
      <button id="google">🔵 Continue with Google</button>
      <p id="msg"></p>
    </div>

    <script type="module">
      import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js";
      import {
        getAuth,
        GoogleAuthProvider,
        signInWithPopup,
      } from "https://www.gstatic.com/firebasejs/10.12.4/firebase-auth.js";

      // TODO: Replace with your Firebase web config (from Firebase Console)
      const firebaseConfig = {
        apiKey: "YOUR_API_KEY_HERE",
        authDomain: "YOUR_AUTH_DOMAIN_HERE",
        projectId: "YOUR_PROJECT_ID_HERE",
        appId: "YOUR_APP_ID_HERE",
      };

      const app = initializeApp(firebaseConfig);
      const auth = getAuth(app);
      const provider = new GoogleAuthProvider();

      const msg = document.getElementById("msg");

      function getReturnUrl() {
        const u = new URL(window.location.href);
        // We will pass return_to=https://vapi-assistant-builder.replit.app
        return u.searchParams.get("return_to") || "https://vapi-assistant-builder.replit.app";
      }

      document.getElementById("google").addEventListener("click", async () => {
        try {
          msg.textContent = "Signing in...";
          const result = await signInWithPopup(auth, provider);
          const token = await result.user.getIdToken();

          // Send token back to Streamlit app as a query param
          const returnTo = getReturnUrl();
          const back = new URL(returnTo);
          back.searchParams.set("id_token", token);
          window.location.href = back.toString();
        } catch (e) {
          console.error(e);
          msg.textContent = `${e.code || "error"}: ${e.message || e}`;
        }
      });
    </script>
  </body>
</html>
```

### Where to get Firebase config:

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (`vapi-demo-auth`)
3. Click the gear icon ⚙️ → **Project settings**
4. Scroll down to **"Your apps"** section
5. Click on the web app (or create one if you don't have it)
6. Copy the `firebaseConfig` object values:
   - `apiKey`
   - `authDomain`
   - `projectId`
   - `appId`

## Step 3: Add Domain to Firebase Authorized Domains

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Go to **Authentication** → **Settings** (gear icon)
4. Scroll down to **"Authorized domains"** section
5. Click **"Add domain"**
6. Add these domains (one at a time):
   - `vapi-login.replit.app` (your login Replit URL - replace with your actual URL)
   - `vapi-assistant-builder.replit.app` (your Streamlit Replit URL - replace with your actual URL)
   - `localhost` (should already be there, but verify)

## Step 4: Configure Environment Variables in Your Streamlit Replit

In your **Streamlit Replit** (the main app), add these environment variables:

1. Click the **🔒 Secrets** (lock icon) in the left sidebar
2. Add these secrets:

   - **Key:** `FIREBASE_LOGIN_PAGE_URL`
     **Value:** `https://vapi-login.replit.app` (replace with your actual login Replit URL)

   - **Key:** `STREAMLIT_APP_URL`
     **Value:** `https://vapi-assistant-builder.replit.app` (replace with your actual Streamlit Replit URL)

3. Click **"Add"** for each secret

## Step 5: Update the Code (Already Done!)

The code has been updated to:
- Link to the external login page instead of using popups
- Handle the `id_token` query parameter when users return
- Verify the token with Firebase Admin SDK

## Step 6: Test the Flow

1. **Start your Streamlit app** in Replit
2. You should see the login/register page
3. Click **"🔵 Continue with Google"**
4. You should be redirected to your login Replit page
5. Click **"🔵 Continue with Google"** on that page
6. Sign in with your Google account
7. You should be redirected back to your Streamlit app
8. You should be logged in!

## Troubleshooting

### "Unauthorized domain" error
- Make sure you added both Replit URLs to Firebase Authorized Domains
- Wait 2-3 minutes after adding domains (propagation delay)
- Check that the URLs match exactly (no trailing slashes, correct subdomain)

### Token verification fails
- Make sure `FIREBASE_SERVICE_ACCOUNT_JSON` is set in your Streamlit Replit secrets
- The service account JSON should be the **entire JSON content** as a string

### Login page doesn't redirect back
- Check that `STREAMLIT_APP_URL` is set correctly in your Streamlit Replit secrets
- Check that `FIREBASE_LOGIN_PAGE_URL` is set correctly
- Verify the `return_to` parameter is being passed correctly

### Button doesn't appear
- Check that Firebase config is set in your Streamlit Replit (all `FIREBASE_*` env vars)
- Check browser console for JavaScript errors

## Summary

✅ **Login Replit**: `https://vapi-login.replit.app` (or your URL)
✅ **Streamlit Replit**: `https://vapi-assistant-builder.replit.app` (or your URL)
✅ **Firebase Authorized Domains**: Both Replit URLs + localhost
✅ **Environment Variables**: `FIREBASE_LOGIN_PAGE_URL` and `STREAMLIT_APP_URL` in Streamlit Replit
✅ **Firebase Config**: Updated in login page HTML

Once all steps are complete, Google Sign-In should work smoothly! 🎉

