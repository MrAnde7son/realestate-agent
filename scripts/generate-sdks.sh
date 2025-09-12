#!/bin/bash

# Generate SDKs and Postman collection from OpenAPI spec
# This script downloads the OpenAPI spec and generates client SDKs

set -e

# Configuration
API_BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
CLIENT_DIR="client"
OPENAPI_SPEC_URL="${API_BASE_URL}/api/docs/openapi.yaml"

echo "🚀 Generating SDKs and Postman collection..."
echo "📡 API Base URL: $API_BASE_URL"
echo "📄 OpenAPI Spec URL: $OPENAPI_SPEC_URL"

# Create client directory if it doesn't exist
mkdir -p "$CLIENT_DIR"

# Download OpenAPI spec
echo "📥 Downloading OpenAPI specification..."
curl -s "$OPENAPI_SPEC_URL" -o "$CLIENT_DIR/openapi.yaml"

if [ ! -s "$CLIENT_DIR/openapi.yaml" ]; then
    echo "❌ Failed to download OpenAPI spec. Make sure the Django server is running."
    exit 1
fi

echo "✅ OpenAPI spec downloaded successfully"

# Check if Docker is available for openapi-generator
if command -v docker &> /dev/null; then
    echo "🐳 Using Docker for OpenAPI Generator..."
    GENERATOR_CMD="docker run --rm -v $(pwd):/local openapitools/openapi-generator-cli"
else
    echo "⚠️  Docker not found. Please install Docker to generate SDKs."
    echo "   You can also install openapi-generator manually:"
    echo "   npm install -g @openapitools/openapi-generator-cli"
    exit 1
fi

# Generate Python SDK
echo "🐍 Generating Python SDK..."
$GENERATOR_CMD generate \
    -i "/local/$CLIENT_DIR/openapi.yaml" \
    -g python \
    -o "/local/$CLIENT_DIR/python" \
    --additional-properties=packageName=realestate_api,projectName=realestate-api,packageVersion=1.0.0,packageUrl=https://github.com/your-org/realestate-agent

# Generate TypeScript SDK
echo "📘 Generating TypeScript SDK..."
$GENERATOR_CMD generate \
    -i "/local/$CLIENT_DIR/openapi.yaml" \
    -g typescript-axios \
    -o "/local/$CLIENT_DIR/typescript" \
    --additional-properties=npmName=@realestate/api-client,npmVersion=1.0.0,withNodeImports=true

# Generate Postman Collection
echo "📮 Generating Postman Collection..."
$GENERATOR_CMD generate \
    -i "/local/$CLIENT_DIR/openapi.yaml" \
    -g postman \
    -o "/local/$CLIENT_DIR/postman" \
    --additional-properties=postmanVariables=[{name:baseUrl,value:${API_BASE_URL}}]

# Create README files
echo "📝 Creating README files..."

# Python SDK README
cat > "$CLIENT_DIR/python/README.md" << 'EOF'
# Real Estate API Python Client

Auto-generated Python client for the Real Estate API.

## Installation

```bash
pip install -e .
```

## Usage

```python
import realestate_api
from realestate_api.api import AssetsApi, PermitsApi, PlansApi
from realestate_api.configuration import Configuration

# Configure the API client
configuration = Configuration()
configuration.host = "http://localhost:8000/api"

# Create API instances
assets_api = AssetsApi(realestate_api.ApiClient(configuration))
permits_api = PermitsApi(realestate_api.ApiClient(configuration))
plans_api = PlansApi(realestate_api.ApiClient(configuration))

# Example: List all assets
try:
    assets = assets_api.assets_list()
    print(f"Found {len(assets.results)} assets")
except Exception as e:
    print(f"Error: {e}")
```

## Authentication

The API uses JWT authentication. Include the access token in the Authorization header:

```python
configuration.api_key['Authorization'] = 'Bearer your-access-token'
configuration.api_key_prefix['Authorization'] = 'Bearer'
```
EOF

# TypeScript SDK README
cat > "$CLIENT_DIR/typescript/README.md" << 'EOF'
# Real Estate API TypeScript Client

Auto-generated TypeScript client for the Real Estate API.

## Installation

```bash
npm install
```

## Usage

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
} catch (error) {
  console.error('Error:', error);
}
```

## Building

```bash
npm run build
```

## Publishing

```bash
npm publish
```
EOF

# Postman Collection README
cat > "$CLIENT_DIR/postman/README.md" << 'EOF'
# Real Estate API Postman Collection

Auto-generated Postman collection for the Real Estate API.

## Import Instructions

1. Open Postman
2. Click "Import" button
3. Select the `Real Estate API.postman_collection.json` file
4. The collection will be imported with all endpoints and example requests

## Environment Variables

The collection uses the following environment variables:

- `baseUrl`: The base URL of the API (default: http://localhost:8000/api)
- `accessToken`: JWT access token for authentication

## Authentication

1. Set the `accessToken` environment variable with your JWT token
2. The collection is configured to use Bearer token authentication
3. Token can be obtained from the `/api/auth/login/` endpoint

## Usage

1. Import the collection
2. Set up environment variables
3. Start with the Authentication folder to get a token
4. Use the token in subsequent requests
EOF

# Create main client README
cat > "$CLIENT_DIR/README.md" << 'EOF'
# Real Estate API Client SDKs

This directory contains auto-generated client SDKs and tools for the Real Estate API.

## Available Clients

- **Python**: `python/` - Python client library
- **TypeScript**: `typescript/` - TypeScript/JavaScript client library  
- **Postman**: `postman/` - Postman collection for API testing

## OpenAPI Specification

The OpenAPI specification is available at:
- YAML: `openapi.yaml`
- JSON: `openapi.json` (if generated)

## Regenerating SDKs

To regenerate the SDKs with the latest API changes:

```bash
./scripts/generate-sdks.sh
```

Make sure the Django server is running on the configured API_BASE_URL.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/docs/redoc/`
- OpenAPI YAML: `http://localhost:8000/api/docs/openapi.yaml`
EOF

echo "✅ SDK generation completed successfully!"
echo ""
echo "📁 Generated files:"
echo "   - Python SDK: $CLIENT_DIR/python/"
echo "   - TypeScript SDK: $CLIENT_DIR/typescript/"
echo "   - Postman Collection: $CLIENT_DIR/postman/"
echo "   - OpenAPI Spec: $CLIENT_DIR/openapi.yaml"
echo ""
echo "🚀 Next steps:"
echo "   1. Test the generated SDKs"
echo "   2. Import the Postman collection"
echo "   3. Update your applications to use the new clients"
