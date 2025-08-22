# Real Estate Broker Dashboard

A modern, professional Next.js 15 dashboard for real estate brokers and agents. Features comprehensive property management, real-time alerts, advanced mortgage analysis, and integrated mapping.

## 🚀 Features

### 🏠 Property Management
- **Advanced assets Table**: Sortable, filterable property assets with pagination
- **Property Details**: Comprehensive property information with tabbed interface
- **Visual Analytics**: Interactive charts and market insights using Recharts
- **Property Images**: Gallery view with property photos
- **Quick Actions**: Save, share, and manage property assets

### 🗺️ Interactive Mapping
- **Mapbox Integration**: High-quality maps with property pins
- **Location Analysis**: Neighborhood insights and proximity data
- **Custom Markers**: Property-specific map markers with details
- **Layer Controls**: Toggle different data layers (schools, transport, etc.)

### 🚨 Real-time Alert System
- **Custom Alert Rules**: Set complex criteria for property notifications
- **Multi-channel Notifications**: Email and WhatsApp alerts
- **Alert Management**: Enable/disable, edit, and track alert performance
- **Instant Notifications**: Real-time alerts when properties match criteria

### 💰 Advanced Mortgage Calculator
- **Affordability Analysis**: Calculate maximum affordable property price
- **Bank of Israel Integration**: Real-time interest rate data
- **Multiple Scenarios**: Compare different down payment amounts
- **Payment Breakdown**: Monthly payments, total interest, and costs
- **Market Comparables**: Integration with government transaction data

### 🎨 Modern UI/UX
- **Responsive Design**: Mobile-friendly interface with adaptive layouts
- **Dark/Light Theme**: Toggle between themes with persistent preferences
- **Professional Design**: Clean, modern interface using Shadcn/ui components
- **RTL Support**: Hebrew language support with proper text direction
- **Accessibility**: WCAG compliant with keyboard navigation

### 📊 Analytics Dashboard
- **Market Insights**: Price trends and market analysis
- **Performance Metrics**: Track asset views and engagement
- **Revenue Analytics**: Commission tracking and financial insights
- **Custom Reports**: Generate detailed market reports

## 🛠️ Tech Stack

### Core Technologies
- **Next.js 15** - App Router with React 19
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Shadcn/ui** - Modern UI component library

### Data & State
- **Zustand** - Lightweight state management
- **React Hook Form** - Forms with validation
- **Zod** - Schema validation
- **nuqs** - URL state management

### Visualization & Maps
- **Recharts** - Chart and data visualization
- **Mapbox GL** - Interactive maps
- **Lucide React** - Modern icon library
- **Tabler Icons** - Additional icon set

### Development
- **Vitest** - Fast testing framework
- **Testing Library** - Component testing utilities
- **ESLint** - Code linting and formatting
- **TypeScript** - Static type checking

## 📋 Prerequisites

- **Node.js 18+** (recommended: 20 LTS)
- **pnpm** (recommended package manager)
- **Django Backend** (for API integration)

## 🚀 Quick Start

### 1️⃣ Installation

```bash
# Navigate to UI directory
cd realestate-broker-ui

# Install dependencies
pnpm install

# Copy environment template
cp .env.example .env.local
```

### 2️⃣ Environment Configuration

Edit `.env.local` with your settings:

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Mapbox Configuration
NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN=your_mapbox_token

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ALERTS=true
NEXT_PUBLIC_ENABLE_MORTGAGE=true

# Debug Settings
NEXT_PUBLIC_DEBUG=false
```

### 3️⃣ Development

```bash
# Start development server
pnpm dev
# Visit http://localhost:3000

# Run tests
pnpm test

# Run linting
pnpm lint

# Build for production
pnpm build
```

### 4️⃣ Backend Setup

Ensure the Django backend is running (see `../backend-django/README.md`):

```bash
# In a separate terminal
cd ../backend-django
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

## 📱 Application Structure

### Page Routes

#### `/` - Dashboard Home
- Property overview and market insights
- Quick action buttons
- Recent activity feed
- Key performance metrics

#### `/assets` - Property assets
- **Features**: Advanced table with sorting, filtering, pagination
- **Actions**: View details, save favorites, export data
- **Filters**: Price range, location, property type, features
- **View Options**: Table, grid, map views

#### `/assets/[id]` - Property Details
- **Overview Tab**: Basic property information and photos
- **Appraisal Tab**: Comparable properties and valuation analysis
- **Rights Tab**: Building rights and zoning information
- **Environment Tab**: Neighborhood data and amenities
- **Finance Tab**: Mortgage calculations and affordability

#### `/alerts` - Alert Management
- **Create Alerts**: Set custom criteria for property notifications
- **Manage Rules**: Edit, enable/disable existing alerts
- **History**: View alert notifications and performance
- **Settings**: Configure notification preferences

#### `/mortgage/analyze` - Mortgage Calculator
- **Affordability Calculator**: Determine maximum property price
- **Scenario Comparison**: Compare different loan terms
- **Market Integration**: Use real market data for calculations
- **Report Generation**: Export detailed affordability reports

#### `/mortgage/boi-calculator` - Bank of Israel Calculator
- **Current Rates**: Real-time interest rate data
- **Rate History**: Historical rate trends
- **Impact Analysis**: How rate changes affect payments

### Component Architecture

#### Layout Components (`components/layout/`)
- **`app-sidebar.tsx`**: Main navigation sidebar with collapsible sections
- **`dashboard-layout.tsx`**: Overall page layout wrapper
- **`header.tsx`**: Top header with user actions and theme toggle
- **`navbar.tsx`**: Primary navigation component

#### UI Components (`components/ui/`)
Built on Shadcn/ui for consistency and accessibility:
- Form controls, buttons, inputs, labels
- Data display: tables, cards, badges
- Navigation: dropdowns, tabs, separators
- Feedback: alerts, progress indicators

#### Feature Components
- **`AssetsTable.tsx`**: Advanced property assets table
- **`Map.tsx`**: Mapbox integration with property pins
- **Theme components**: Dark/light mode support

### Data Management

#### State Management (`lib/`)
- **`data.ts`**: TypeScript interfaces and data models
- **`config.ts`**: Application configuration and constants
- **`mortgage.ts`**: Mortgage calculation utilities
- **`utils.ts`**: Shared utility functions

#### API Integration
- RESTful API calls to Django backend
- Type-safe data fetching with Zod validation
- Error handling and loading states
- Optimistic updates for better UX

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pnpm test

# Watch mode during development
pnpm test:watch

# Coverage report
pnpm test:coverage
```

### Test Structure
- **Unit Tests**: Component logic and utilities
- **Integration Tests**: API integration and data flow
- **E2E Tests**: Full user workflows (planned)

### Example Test Files
- `app/assets/page.test.tsx` - assets page functionality
- `app/alerts/page.test.tsx` - Alert system testing
- `components/Map.test.tsx` - Map component testing

## 🎨 Design System

### Theme Configuration
Comprehensive theme system with support for:
- **Colors**: Primary, secondary, accent colors with variants
- **Typography**: Font families, sizes, weights, line heights
- **Spacing**: Consistent margin, padding, and gap values
- **Borders**: Radius, width, and style definitions
- **Shadows**: Elevation and depth effects

### RTL Support
Full Hebrew language support:
- **Text Direction**: Automatic RTL text flow
- **Layout Mirroring**: UI elements flip appropriately
- **Font Support**: Hebrew font families and character sets

### Responsive Design
Mobile-first approach with breakpoints:
- **Mobile**: 320px+ (base styles)
- **Tablet**: 768px+ (md breakpoint)
- **Desktop**: 1024px+ (lg breakpoint)
- **Large Desktop**: 1280px+ (xl breakpoint)

## 🔌 API Integration

### Endpoint Usage

#### Property assets
```typescript
// Fetch assets with filters
const response = await fetch(`${API_BASE}/api/assets/?city=5000&max_price=8000000`);
const assets = await response.json();

// Get property details
const property = await fetch(`${API_BASE}/api/assets/${id}/`);
```

#### Alert Management
```typescript
// Create new alert
const alert = await fetch(`${API_BASE}/api/alerts/`, {
  method: 'POST',
  body: JSON.stringify({
    name: 'Tel Aviv Apartments',
    criteria: { city: 5000, rooms: '4' },
    email_enabled: true
  })
});
```

#### Mortgage Analysis
```typescript
// Calculate affordability
const analysis = await fetch(`${API_BASE}/api/mortgage/analyze/`, {
  method: 'POST',
  body: JSON.stringify({
    property_price: 4500000,
    down_payment: 900000,
    monthly_income: 25000
  })
});
```

## 📊 Analytics Integration

### Performance Monitoring
- **Core Web Vitals**: LCP, FID, CLS tracking
- **User Interactions**: Click tracking and engagement metrics
- **Error Reporting**: Automatic error boundary reporting

### Business Metrics
- **Property Views**: Track most viewed properties
- **Alert Performance**: Monitor alert accuracy and engagement
- **User Behavior**: Page flow and conversion tracking

## 🚀 Deployment

### Build Process

```bash
# Production build
pnpm build

# Start production server
pnpm start

# Static export (optional)
pnpm export
```

### Environment Variables

**Production Settings:**
```env
NEXT_PUBLIC_API_BASE_URL=https://api.yourbroker.com
NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN=your_production_token
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_ANALYTICS_ID=your_analytics_id
```

### Deployment Platforms
- **Vercel**: Optimized for Next.js (recommended)
- **Netlify**: Static site deployment
- **Docker**: Containerized deployment
- **AWS/GCP**: Cloud platform deployment

## 🔧 Development Workflow

### Code Style
- **Prettier**: Automatic code formatting
- **ESLint**: Comprehensive linting rules
- **TypeScript**: Strict type checking
- **Commit Hooks**: Pre-commit quality checks

### Git Workflow
- **Feature Branches**: One feature per branch
- **Pull Requests**: Code review before merge
- **Semantic Commits**: Conventional commit messages
- **Automated Testing**: CI/CD integration

## 📝 Contributing

### Getting Started
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- Follow TypeScript best practices
- Use functional components with hooks
- Implement responsive design
- Add proper error handling
- Include comprehensive tests

## 🆘 Troubleshooting

### Common Issues

#### API Connection Problems
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Verify environment variables
echo $NEXT_PUBLIC_API_BASE_URL
```

#### Build Errors
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

#### Map Integration Issues
- Verify Mapbox token is valid
- Check browser console for API errors
- Ensure HTTPS for production deployments

### Performance Issues
- Use React DevTools Profiler
- Check bundle size with `pnpm build --analyze`
- Monitor Core Web Vitals in production

## 📚 Additional Resources

- **Next.js Documentation**: https://nextjs.org/docs
- **Shadcn/ui Components**: https://ui.shadcn.com
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Mapbox GL**: https://docs.mapbox.com/mapbox-gl-js
