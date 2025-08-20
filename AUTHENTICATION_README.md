# Authentication System for Real Estate Agent

This document explains how to set up and use the new authentication system implemented in the real estate application.

## Overview

The authentication system provides:
- User registration and login
- JWT-based authentication
- Protected routes
- User profile management
- Role-based access control

## Backend Setup

### 1. Install Dependencies

First, install the required Django packages:

```bash
cd backend-django
pip install -r requirements.txt
```

### 2. Database Setup

Run the setup script to initialize the database and create test users:

```bash
cd backend-django
python setup_auth.py
```

This will:
- Create the database tables
- Create a superuser (admin@example.com / admin123)
- Create a test user (demo@example.com / demo123)

### 3. Start the Backend

```bash
cd backend-django
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

## Frontend Setup

### 1. Install Dependencies

```bash
cd realestate-broker-ui
npm install
# or
pnpm install
```

### 2. Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start the Frontend

```bash
cd realestate-broker-ui
npm run dev
# or
pnpm dev
```

The frontend will be available at `http://localhost:3000`

## How to Use

### 1. Registration

1. Navigate to `/auth`
2. Click on "הרשמה" (Register) tab
3. Fill in the required fields:
   - Email
   - Username
   - Password
   - First Name
   - Last Name
   - Company (optional)
   - Role (optional)
4. Click "הירשם" (Register)

### 2. Login

1. Navigate to `/auth`
2. Use the "התחברות" (Login) tab
3. Enter your email and password
4. Click "התחבר" (Login)

### 3. Protected Routes

After login, you can access:
- `/` - Home dashboard
- `/listings` - Property listings
- `/alerts` - Market alerts
- `/mortgage/analyze` - Mortgage calculator
- `/reports` - Property reports
- `/profile` - User profile

### 4. User Profile

1. Click on your avatar in the sidebar
2. Select "פרופיל" (Profile)
3. Click "ערוך" (Edit) to modify your information
4. Save changes

### 5. Logout

1. Click on your avatar in the sidebar
2. Select "התנתק" (Logout)

## API Endpoints

### Authentication

- `POST /api/auth/login/` - User registration
- `POST /api/auth/register/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/profile/update/` - Update user profile
- `POST /api/auth/refresh/` - Refresh JWT token

### Protected Endpoints

All other endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Security Features

- JWT tokens with configurable expiration
- Password validation and hashing
- Protected routes with middleware
- CSRF protection
- Secure password requirements

## User Roles

The system supports different user roles:
- **מנהל מערכת** (System Administrator) - Full access
- **מתווך נדל״ן** (Real Estate Broker) - Standard access
- **שמאי** (Appraiser) - Appraisal tools access
- **משקיע** (Investor) - Investment analysis tools

## Customization

### Adding New User Fields

1. Update the User model in `backend-django/core/models.py`
2. Run migrations: `python manage.py makemigrations && python manage.py migrate`
3. Update the frontend forms and interfaces

### Changing Authentication Settings

Modify JWT settings in `backend-django/broker_backend/settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # ... other settings
}
```

### Adding New Protected Routes

Update the middleware in `realestate-broker-ui/middleware.ts`:

```typescript
const protectedRoutes = [
  '/',
  '/listings',
  '/alerts',
  '/mortgage',
  '/reports',
  '/profile',
  '/billing',
  '/settings',
  '/your-new-route'  // Add new protected routes here
]
```

## Troubleshooting

### Common Issues

1. **"Invalid credentials" error**
   - Check if the user exists in the database
   - Verify password is correct
   - Ensure the backend is running

2. **"Token expired" error**
   - The JWT token has expired
   - User needs to log in again
   - Check JWT lifetime settings

3. **"Route not found" error**
   - Ensure the backend is running
   - Check if the route is properly configured in Django URLs
   - Verify the frontend API URL is correct

4. **Database connection issues**
   - Check if the database file exists
   - Ensure proper permissions
   - Run the setup script again

### Debug Mode

Enable debug mode in Django settings for detailed error messages:

```python
DEBUG = True
```

## Testing

### Backend Tests

```bash
cd backend-django
python manage.py test
```

### Frontend Tests

```bash
cd realestate-broker-ui
npm test
# or
pnpm test
```

## Production Considerations

1. **Change default passwords** for admin and demo users
2. **Set DEBUG = False** in production
3. **Use environment variables** for sensitive settings
4. **Enable HTTPS** for secure communication
5. **Implement rate limiting** for API endpoints
6. **Add logging** for security events
7. **Regular security updates** for dependencies

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django and Next.js documentation
3. Check the application logs
4. Verify environment configuration
