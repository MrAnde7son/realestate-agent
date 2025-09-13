#!/usr/bin/env python3
"""
Generate SDKs and Postman collection from OpenAPI spec.
This script can work with or without Docker.
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
from typing import Optional

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CLIENT_DIR = Path("client")
OPENAPI_SPEC_URL = f"{API_BASE_URL}/api/docs/openapi.yaml"


def run_command(cmd: list, cwd: Optional[Path] = None) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def check_docker() -> bool:
    """Check if Docker is available."""
    success, _ = run_command(["docker", "--version"])
    return success


def check_openapi_generator() -> bool:
    """Check if openapi-generator is available via npm."""
    success, _ = run_command(["npx", "openapi-generator-cli", "version"])
    return success


def download_openapi_spec() -> bool:
    """Download the OpenAPI specification."""
    print("📥 Downloading OpenAPI specification...")
    
    try:
        response = requests.get(OPENAPI_SPEC_URL, timeout=30)
        response.raise_for_status()
        
        CLIENT_DIR.mkdir(exist_ok=True)
        spec_path = CLIENT_DIR / "openapi.yaml"
        
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        if spec_path.stat().st_size == 0:
            print("❌ Downloaded OpenAPI spec is empty")
            return False
            
        print("✅ OpenAPI spec downloaded successfully")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Failed to download OpenAPI spec: {e}")
        print("   Make sure the Django server is running on", API_BASE_URL)
        return False


def generate_with_docker(spec_path: Path) -> bool:
    """Generate SDKs using Docker."""
    print("🐳 Using Docker for OpenAPI Generator...")
    
    generator_cmd = [
        "docker", "run", "--rm",
        "-v", f"{Path.cwd()}:/local",
        "openapitools/openapi-generator-cli"
    ]
    
    # Generate Python SDK
    print("🐍 Generating Python SDK...")
    python_cmd = generator_cmd + [
        "generate",
        "-i", f"/local/{spec_path}",
        "-g", "python",
        "-o", "/local/client/python",
        "--additional-properties=packageName=realestate_api,projectName=realestate-api,packageVersion=1.0.0"
    ]
    
    success, output = run_command(python_cmd)
    if not success:
        print(f"❌ Failed to generate Python SDK: {output}")
        return False
    
    # Generate TypeScript SDK
    print("📘 Generating TypeScript SDK...")
    ts_cmd = generator_cmd + [
        "generate",
        "-i", f"/local/{spec_path}",
        "-g", "typescript-axios",
        "-o", "/local/client/typescript",
        "--additional-properties=npmName=@realestate/api-client,npmVersion=1.0.0"
    ]
    
    success, output = run_command(ts_cmd)
    if not success:
        print(f"❌ Failed to generate TypeScript SDK: {output}")
        return False
    
    # Generate Postman Collection
    print("📮 Generating Postman Collection...")
    postman_cmd = generator_cmd + [
        "generate",
        "-i", f"/local/{spec_path}",
        "-g", "postman",
        "-o", "/local/client/postman",
        f"--additional-properties=postmanVariables=[{{name:baseUrl,value:{API_BASE_URL}}}]"
    ]
    
    success, output = run_command(postman_cmd)
    if not success:
        print(f"❌ Failed to generate Postman collection: {output}")
        return False
    
    return True


def generate_with_npm(spec_path: Path) -> bool:
    """Generate SDKs using npm openapi-generator-cli."""
    print("📦 Using npm openapi-generator-cli...")
    
    # Generate Python SDK
    print("🐍 Generating Python SDK...")
    python_cmd = [
        "npx", "openapi-generator-cli", "generate",
        "-i", str(spec_path),
        "-g", "python",
        "-o", "client/python",
        "--additional-properties=packageName=realestate_api,projectName=realestate-api,packageVersion=1.0.0"
    ]
    
    success, output = run_command(python_cmd)
    if not success:
        print(f"❌ Failed to generate Python SDK: {output}")
        return False
    
    # Generate TypeScript SDK
    print("📘 Generating TypeScript SDK...")
    ts_cmd = [
        "npx", "openapi-generator-cli", "generate",
        "-i", str(spec_path),
        "-g", "typescript-axios",
        "-o", "client/typescript",
        "--additional-properties=npmName=@realestate/api-client,npmVersion=1.0.0"
    ]
    
    success, output = run_command(ts_cmd)
    if not success:
        print(f"❌ Failed to generate TypeScript SDK: {output}")
        return False
    
    # Generate Postman Collection
    print("📮 Generating Postman Collection...")
    postman_cmd = [
        "npx", "openapi-generator-cli", "generate",
        "-i", str(spec_path),
        "-g", "postman",
        "-o", "client/postman",
        f"--additional-properties=postmanVariables=[{{name:baseUrl,value:{API_BASE_URL}}}]"
    ]
    
    success, output = run_command(postman_cmd)
    if not success:
        print(f"❌ Failed to generate Postman collection: {output}")
        return False
    
    return True


def create_readme_files():
    """Create README files for the generated SDKs."""
    print("📝 Creating README files...")
    
    # Python SDK README
    python_readme = CLIENT_DIR / "python" / "README.md"
    python_readme.write_text("""# Real Estate API Python Client

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
""")
    
    # TypeScript SDK README
    ts_readme = CLIENT_DIR / "typescript" / "README.md"
    ts_readme.write_text("""# Real Estate API TypeScript Client

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
""")
    
    # Postman Collection README
    postman_readme = CLIENT_DIR / "postman" / "README.md"
    postman_readme.write_text("""# Real Estate API Postman Collection

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
""")
    
    # Main client README
    main_readme = CLIENT_DIR / "README.md"
    main_readme.write_text(f"""# Real Estate API Client SDKs

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
python scripts/generate-sdks.py
```

Or using the shell script:

```bash
./scripts/generate-sdks.sh
```

Make sure the Django server is running on the configured API_BASE_URL.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `{API_BASE_URL}/api/docs/`
- ReDoc: `{API_BASE_URL}/api/docs/redoc/`
- OpenAPI YAML: `{API_BASE_URL}/api/docs/openapi.yaml`
""")


def main():
    """Main function to generate SDKs."""
    print("🚀 Generating SDKs and Postman collection...")
    print(f"📡 API Base URL: {API_BASE_URL}")
    print(f"📄 OpenAPI Spec URL: {OPENAPI_SPEC_URL}")
    
    # Download OpenAPI spec
    if not download_openapi_spec():
        sys.exit(1)
    
    spec_path = CLIENT_DIR / "openapi.yaml"
    
    # Try to generate SDKs
    success = False
    
    if check_docker():
        success = generate_with_docker(spec_path)
    elif check_openapi_generator():
        success = generate_with_npm(spec_path)
    else:
        print("❌ Neither Docker nor npm openapi-generator-cli is available.")
        print("   Please install one of the following:")
        print("   1. Docker: https://docs.docker.com/get-docker/")
        print("   2. npm: npm install -g @openapitools/openapi-generator-cli")
        sys.exit(1)
    
    if not success:
        print("❌ SDK generation failed")
        sys.exit(1)
    
    # Create README files
    create_readme_files()
    
    print("✅ SDK generation completed successfully!")
    print("")
    print("📁 Generated files:")
    print("   - Python SDK: client/python/")
    print("   - TypeScript SDK: client/typescript/")
    print("   - Postman Collection: client/postman/")
    print("   - OpenAPI Spec: client/openapi.yaml")
    print("")
    print("🚀 Next steps:")
    print("   1. Test the generated SDKs")
    print("   2. Import the Postman collection")
    print("   3. Update your applications to use the new clients")


if __name__ == "__main__":
    main()
