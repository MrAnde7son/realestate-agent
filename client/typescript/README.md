# Real Estate API TypeScript Client

TypeScript client for the Real Estate API.

## Installation

```bash
cd client/typescript
npm install
```

## Usage

```typescript
import { RealEstateAPIClient } from './src';

// Initialize the client
const client = new RealEstateAPIClient('http://localhost:8000/api');

// Login to get authentication token
const loginResponse = await client.login({
  email: 'user@example.com',
  password: 'password123'
});
console.log(`Logged in as: ${loginResponse.user.email}`);

// List all assets
const assets = await client.getAssets();
console.log(`Found ${assets.data?.length || 0} assets`);

// Create a new asset
const newAsset = await client.createAsset({
  address: '123 Main St',
  street: 'Main St',
  number: 123,
  city: 'Tel Aviv'
});
console.log(`Created asset with ID: ${newAsset.id}`);

// Get specific asset
const asset = await client.getAsset(newAsset.id);
console.log(`Asset address: ${asset.address}`);
```

## Authentication

The API uses JWT authentication. You can either:

1. **Login with credentials** (recommended):
```typescript
const client = new RealEstateAPIClient();
await client.login({ email: 'email@example.com', password: 'password' });
```

2. **Set token directly**:
```typescript
const client = new RealEstateAPIClient('http://localhost:8000/api', 'your-jwt-token');
```

## Available Methods

### Authentication
- `login(credentials: LoginRequest)` - Login with credentials
- `register(userData: RegisterRequest)` - Register new user
- `refreshToken(refreshToken: string)` - Refresh access token
- `logout()` - Logout current user
- `getProfile()` - Get user profile
- `updateProfile(data: Record<string, any>)` - Update user profile

### Assets
- `getAssets(params?: Record<string, string>)` - List all assets
- `getAsset(assetId: number)` - Get specific asset
- `createAsset(data: Partial<Asset>)` - Create new asset
- `updateAsset(assetId: number, data: Partial<Asset>)` - Update asset
- `deleteAsset(assetId: number)` - Delete asset
- `getAssetStats()` - Get asset statistics

### Permits
- `getPermits(params?: Record<string, string>)` - List all permits
- `getPermit(permitId: number)` - Get specific permit
- `createPermit(data: Partial<Permit>)` - Create new permit
- `updatePermit(permitId: number, data: Partial<Permit>)` - Update permit
- `deletePermit(permitId: number)` - Delete permit

### Plans
- `getPlans(params?: Record<string, string>)` - List all plans
- `getPlan(planId: number)` - Get specific plan
- `createPlan(data: Partial<Plan>)` - Create new plan
- `updatePlan(planId: number, data: Partial<Plan>)` - Update plan
- `deletePlan(planId: number)` - Delete plan

### Additional Methods
- `analyzeMortgage(data: Record<string, any>)` - Analyze mortgage data
- `syncAddress(data: Record<string, any>)` - Sync address data
- `getTabu(params?: Record<string, string>)` - Get tabu information
- `getReports(params?: Record<string, string>)` - Get reports
- `getAlerts()` - Get alerts
- `createAlert(data: Record<string, any>)` - Create alert
- `getAnalyticsTimeseries(params?: Record<string, string>)` - Get analytics data

## Error Handling

The client throws specific exceptions for different error types:

```typescript
import { AuthenticationError, ValidationError, NotFoundError } from './src';

try {
  await client.getAsset(999); // Non-existent asset
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log('Asset not found');
  } else if (error instanceof AuthenticationError) {
    console.log('Please login first');
  } else if (error instanceof ValidationError) {
    console.log(`Invalid data: ${error.message}`);
  }
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
