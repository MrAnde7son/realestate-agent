# OpenAPI Specification and SDKs

This document describes the OpenAPI specification and auto-generated SDKs for the Real Estate API.

## Overview

The Real Estate API provides a comprehensive REST API for managing real estate assets, permits, plans, and related data. The API is documented using OpenAPI 3.0 specification and includes auto-generated client SDKs for multiple programming languages.

## API Documentation

### Interactive Documentation

To view documentation for non-local environments, update the base URL accordingly (e.g., \`https://staging.nadlaner.com\` or \`https://api.nadlaner.com\`).

- **Swagger UI (local)**: `http://localhost:8000/api/docs/` - Interactive API explorer
- **Swagger UI (staging)**: `https://staging.nadlaner.com/api/docs/` - Staging environment
- **Swagger UI (production)**: `https://api.nadlaner.com/api/docs/` - Production environment
- **ReDoc (local)**: `http://localhost:8000/api/docs/redoc/` - Clean, responsive documentation
- **ReDoc (staging)**: `https://staging.nadlaner.com/api/docs/redoc/` - Staging environment
- **ReDoc (production)**: `https://api.nadlaner.com/api/docs/redoc/` - Production environment
- **OpenAPI YAML (local)**: `http://localhost:8000/api/docs/openapi.yaml` - Raw specification
- **OpenAPI YAML (staging)**: `https://staging.nadlaner.com/api/docs/openapi.yaml`
- **OpenAPI YAML (production)**: `https://api.nadlaner.com/api/docs/openapi.yaml`

### API Endpoints

The API is organized into the following main categories:

#### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PUT /api/auth/update-profile/` - Update user profile
- `POST /api/auth/refresh/` - Refresh JWT token
- `GET /api/auth/google/login/` - Google OAuth login
- `GET /api/auth/google/callback/` - Google OAuth callback

#### Assets
- `GET /api/assets/` - List all assets
- `POST /api/assets/` - Create new asset
- `GET /api/assets/{id}/` - Get asset details
- `PUT /api/assets/{id}/` - Update asset
- `PATCH /api/assets/{id}/` - Partially update asset
- `DELETE /api/assets/{id}/` - Delete asset
- `GET /api/assets/stats/` - Get asset statistics

#### Permits
- `GET /api/permits/` - List all permits
- `POST /api/permits/` - Create new permit
- `GET /api/permits/{id}/` - Get permit details
- `PUT /api/permits/{id}/` - Update permit
- `PATCH /api/permits/{id}/` - Partially update permit
- `DELETE /api/permits/{id}/` - Delete permit

#### Plans
- `GET /api/plans/` - List all plans
- `POST /api/plans/` - Create new plan
- `GET /api/plans/{id}/` - Get plan details
- `PUT /api/plans/{id}/` - Update plan
- `PATCH /api/plans/{id}/` - Partially update plan
- `DELETE /api/plans/{id}/` - Delete plan

#### Additional Endpoints
- `POST /api/mortgage-analyze/` - Mortgage analysis
- `POST /api/sync-address/` - Address synchronization
- `GET /api/tabu/` - Tabu information
- `GET /api/reports/` - Generate reports
- `GET /api/alerts/` - Alert management
- `GET /api/analytics/timeseries` - Analytics data

## Generated SDKs

### Python SDK

**Location**: `client/python/`

**Installation**:
```bash
cd client/python
pip install -e .
```

**Usage**:
```python
import realestate_api
from realestate_api.api import AssetsApi, PermitsApi, PlansApi
from realestate_api.configuration import Configuration

# Configure the API client
configuration = Configuration()
configuration.host = "http://localhost:8000/api"

# Set up authentication
configuration.api_key['Authorization'] = 'Bearer your-access-token'
configuration.api_key_prefix['Authorization'] = 'Bearer'

# Create API instances
assets_api = AssetsApi(realestate_api.ApiClient(configuration))
permits_api = PermitsApi(realestate_api.ApiClient(configuration))
plans_api = PlansApi(realestate_api.ApiClient(configuration))

# Example: List all assets
try:
    assets = assets_api.assets_list()
    print(f"Found {len(assets.results)} assets")
    for asset in assets.results:
        print(f"- {asset.address} (ID: {asset.id})")
except Exception as e:
    print(f"Error: {e}")
```

### TypeScript SDK

**Location**: `client/typescript/`

**Installation**:
```bash
cd client/typescript
npm install
```

**Usage**:
```typescript
import { Configuration, AssetsApi, PermitsApi, PlansApi } from './src';

// Configure the API client
const configuration = new Configuration({
  basePath: 'http://localhost:8000/api',
  accessToken: 'your-access-token'
});

// Create API instances
const assetsApi = new AssetsApi(configuration);
const permitsApi = new PermitsApi(configuration);
const plansApi = new PlansApi(configuration);

// Example: List all assets
try {
  const assets = await assetsApi.assetsList();
  console.log(`Found ${assets.data.results?.length} assets`);
  assets.data.results?.forEach(asset => {
    console.log(`- ${asset.address} (ID: ${asset.id})`);
  });
} catch (error) {
  console.error('Error:', error);
}
```

### Postman Collection

**Location**: `client/postman/`

**Import Instructions**:
1. Open Postman
2. Click "Import" button
3. Select the `Real Estate API.postman_collection.json` file
4. Set up environment variables:
   - `baseUrl`: `http://localhost:8000/api`
   - `accessToken`: Your JWT token

## Regenerating SDKs

### Using the Python Script (Recommended)

```bash
python scripts/generate-sdks.py
```

### Using the Shell Script

```bash
./scripts/generate-sdks.sh
```

### Prerequisites

You need either:
- **Docker**: `docker --version` (recommended)
- **npm**: `npm install -g @openapitools/openapi-generator-cli`

### Environment Variables

- `API_BASE_URL`: Base URL of the API (default: `http://localhost:8000`)

## Testing the API

### Test OpenAPI Endpoints

```bash
python scripts/test-openapi.py
```

This will test:
- OpenAPI YAML spec availability
- Swagger UI accessibility
- ReDoc accessibility
- Basic API endpoints

### Manual Testing

1. Start the Django server:
   ```bash
   cd backend-django
   python manage.py runserver
   ```

2. Visit the documentation:
   - Swagger UI: http://localhost:8000/api/docs/
   - ReDoc: http://localhost:8000/api/docs/redoc/

3. Test authentication:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "password"}'
   ```

## API Authentication

The API uses JWT (JSON Web Token) authentication:

1. **Login**: `POST /api/auth/login/` with email/password
2. **Get Token**: Response includes `access` and `refresh` tokens
3. **Use Token**: Include `Authorization: Bearer <access_token>` header
4. **Refresh Token**: Use `POST /api/auth/refresh/` when access token expires

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

Error responses include a JSON object with error details:

```json
{
  "error": "Error message",
  "detail": "Additional error details"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Current limits:
- 1000 requests per hour per IP
- 100 requests per minute per authenticated user

## Data Models

### Asset
- `id`: Unique identifier
- `address`: Property address
- `street`: Street name
- `number`: Street number
- `city`: City name
- `normalized_address`: Standardized address
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Permit
- `id`: Unique identifier
- `permit_number`: Official permit number
- `status`: Permit status
- `issue_date`: Date issued
- `expiry_date`: Expiration date
- `description`: Permit description

### Plan
- `id`: Unique identifier
- `plan_number`: Official plan number
- `title`: Plan title
- `status`: Plan status
- `approval_date`: Date approved
- `description`: Plan description

## Contributing

When adding new API endpoints:

1. Add proper OpenAPI documentation using `@extend_schema` decorators
2. Include appropriate tags and descriptions
3. Add request/response examples
4. Update this documentation
5. Regenerate SDKs using the provided scripts

## Support

For API support and questions:
- Check the interactive documentation at `/api/docs/`
- Review the generated SDK examples
- Contact the development team
