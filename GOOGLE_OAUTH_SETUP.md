# 🔐 Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for your real estate application.

## 🚀 **What's Been Implemented**

✅ **Backend (Django)**
- Google OAuth endpoints (`/api/auth/google/login/` and `/api/auth/google/callback/`)
- Automatic user creation for new Google users
- JWT token generation for authenticated users
- Secure token exchange with Google

✅ **Frontend (Next.js)**
- Google login button on the auth page
- OAuth callback handling page
- Integration with existing authentication system
- Automatic redirect after successful authentication

## 📋 **Prerequisites**

1. **Google Cloud Console Account**
2. **Django Backend Running** (port 8000)
3. **Next.js Frontend Running** (port 3000)

## 🔧 **Step 1: Google Cloud Console Setup**

### 1.1 Create a New Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it something like "Real Estate App OAuth"
4. Click "Create"

### 1.2 Enable Google+ API
1. In the left sidebar, go to "APIs & Services" → "Library"
2. Search for "Google+ API" or "Google Identity"
3. Click on it and click "Enable"

### 1.3 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen first:
   - User Type: External
   - App name: "Real Estate App"
   - User support email: Your email
   - Developer contact information: Your email
   - Save and continue

4. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: "Real Estate App Web Client"
   - Authorized redirect URIs: `http://localhost:8000/api/auth/google/callback/`
   - Click "Create"

5. **Save your Client ID and Client Secret!**

## 🔧 **Step 2: Environment Configuration**

### 2.1 Backend Environment Variables
Create a `.env` file in the `backend-django` directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth Settings
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

> The backend builds the OAuth callback URL automatically, so no `GOOGLE_REDIRECT_URI` variable is required.

### 2.2 Frontend Environment Variables
Create a `.env.local` file in the `realestate-broker-ui` directory:

```env
# API Configuration
BACKEND_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ALERTS=true
NEXT_PUBLIC_ENABLE_MORTGAGE=true

# Debug Settings
NEXT_PUBLIC_DEBUG=true
```

## 🚀 **Step 3: Start the Servers**

### 3.1 Start Django Backend
```bash
cd backend-django
python3 manage.py runserver 0.0.0.0:8000
```

### 3.2 Start Next.js Frontend
```bash
cd realestate-broker-ui
npm run dev
```

## 🧪 **Step 4: Test Google OAuth**

1. **Open your browser** and go to `http://localhost:3000/auth`
2. **Click the "התחבר עם Google" (Login with Google) button**
3. **You'll be redirected to Google's OAuth consent screen**
4. **Sign in with your Google account**
5. **Grant permissions** to the application
6. **You'll be redirected back** to the app and automatically logged in!

## 🔍 **How It Works**

### **Flow Diagram:**
```
User clicks "Login with Google"
         ↓
Frontend calls /api/auth/google/login/
         ↓
Backend returns Google OAuth URL
         ↓
Frontend redirects to Google
         ↓
User authenticates with Google
         ↓
Google redirects to /api/auth/google/callback/
         ↓
Backend exchanges code for tokens
         ↓
Backend gets user info from Google
         ↓
Backend creates/updates user in database
         ↓
Backend generates JWT tokens
         ↓
Backend redirects to frontend with tokens
         ↓
Frontend stores tokens and logs user in
         ↓
User is redirected to home page
```

## 🛠️ **Troubleshooting**

### **Common Issues:**

1. **"Invalid redirect_uri" error**
   - Make sure the redirect URI in Google Console exactly matches: `http://localhost:8000/api/auth/google/callback/`
   - Check for trailing slashes and protocol (http vs https)

2. **"Client ID not found" error**
   - Verify your `GOOGLE_CLIENT_ID` in the `.env` file
   - Make sure you copied the entire client ID

3. **"Client secret invalid" error**
   - Verify your `GOOGLE_CLIENT_SECRET` in the `.env` file
   - Make sure there are no extra spaces

4. **CORS errors**
   - Ensure Django backend is running on port 8000
   - Check that `CORS_ALLOW_ALL_ORIGINS = True` is set in Django settings

5. **Frontend not redirecting**
   - Check browser console for JavaScript errors
   - Verify the frontend is running on port 3000
   - Check that the `.env.local` file is created correctly

### **Debug Steps:**

1. **Check Django logs** for backend errors
2. **Check browser console** for frontend errors
3. **Verify environment variables** are loaded correctly
4. **Test API endpoints** directly with curl or Postman

## 🔒 **Security Considerations**

1. **Never commit your `.env` files** to version control
2. **Use strong, unique Client Secrets**
3. **Limit OAuth scopes** to only what's necessary
4. **Implement proper error handling** for production
5. **Consider rate limiting** for OAuth endpoints
6. **Use HTTPS in production**

## 🚀 **Production Deployment**

For production, you'll need to:

1. **Update redirect URIs** in Google Console to your production domain
2. **Set environment variables** on your production server
3. **Use HTTPS** for all OAuth flows
4. **Implement proper error logging**
5. **Add monitoring** for OAuth failures

## 📚 **Additional Resources**

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [Next.js Authentication](https://nextjs.org/docs/authentication)

## 🎯 **Next Steps**

After setting up Google OAuth, you can:

1. **Add more OAuth providers** (Facebook, GitHub, etc.)
2. **Implement social login buttons** with proper styling
3. **Add user profile picture** from Google account
4. **Implement account linking** for existing users
5. **Add OAuth logout** functionality

---

**Need help?** Check the troubleshooting section above or review the error logs in your browser console and Django server output.
