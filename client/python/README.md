# Real Estate API Python Client

Python client for the Real Estate API.

## Installation

```bash
cd client/python
pip install -e .
```

## Usage

```python
from realestate_api import RealEstateAPIClient

# Initialize the client
client = RealEstateAPIClient(base_url="http://localhost:8000/api")

# Login to get authentication token
login_response = client.login("user@example.com", "password123")
print(f"Logged in as: {login_response['user']['email']}")

# List all assets
assets = client.get_assets()
print(f"Found {len(assets.get('data', []))} assets")

# Create a new asset
new_asset = client.create_asset({
    "address": "123 Main St",
    "street": "Main St", 
    "number": 123,
    "city": "Tel Aviv"
})
print(f"Created asset with ID: {new_asset['id']}")

# Get specific asset
asset = client.get_asset(new_asset['id'])
print(f"Asset address: {asset['address']}")
```

## Authentication

The API uses JWT authentication. You can either:

1. **Login with credentials** (recommended):
```python
client = RealEstateAPIClient()
client.login("email@example.com", "password")
```

2. **Set token directly**:
```python
client = RealEstateAPIClient(token="your-jwt-token")
```

## Available Methods

### Authentication
- `login(email, password)` - Login with credentials
- `register(email, password, username, **kwargs)` - Register new user
- `refresh_token(refresh_token)` - Refresh access token
- `logout()` - Logout current user
- `get_profile()` - Get user profile
- `update_profile(**data)` - Update user profile

### Assets
- `get_assets(**params)` - List all assets
- `get_asset(asset_id)` - Get specific asset
- `create_asset(**data)` - Create new asset
- `update_asset(asset_id, **data)` - Update asset
- `delete_asset(asset_id)` - Delete asset
- `get_asset_stats()` - Get asset statistics

### Permits
- `get_permits(**params)` - List all permits
- `get_permit(permit_id)` - Get specific permit
- `create_permit(**data)` - Create new permit
- `update_permit(permit_id, **data)` - Update permit
- `delete_permit(permit_id)` - Delete permit

### Plans
- `get_plans(**params)` - List all plans
- `get_plan(plan_id)` - Get specific plan
- `create_plan(**data)` - Create new plan
- `update_plan(plan_id, **data)` - Update plan
- `delete_plan(plan_id)` - Delete plan

### Additional Methods
- `analyze_mortgage(**data)` - Analyze mortgage data
- `sync_address(**data)` - Sync address data
- `get_tabu(**params)` - Get tabu information
- `get_reports(**params)` - Get reports
- `get_alerts()` - Get alerts
- `create_alert(**data)` - Create alert
- `get_analytics_timeseries(**params)` - Get analytics data

## Error Handling

The client raises specific exceptions for different error types:

```python
from realestate_api.exceptions import AuthenticationError, ValidationError, NotFoundError

try:
    client.get_asset(999)  # Non-existent asset
except NotFoundError:
    print("Asset not found")
except AuthenticationError:
    print("Please login first")
except ValidationError as e:
    print(f"Invalid data: {e}")
```
