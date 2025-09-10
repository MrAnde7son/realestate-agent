# Real Estate Agent Monorepo Development Checklist

## 🏗️ Project Structure Overview

This monorepo contains:
- **Frontend**: Next.js React app (`realestate-broker-ui/`)
- **Backend**: Django REST API (`backend-django/`)
- **Data Services**: Python services for data collection
  - `yad2/` - Yad2 real estate scraping
  - `gov/` - Government data (nadlan, decisive)
  - `mavat/` - Planning data collection
  - `rami/` - RAMI planning system
  - `gis/` - GIS data processing
- **Orchestration**: Data pipeline and scheduling (`orchestration/`)
- **Database**: Shared database models (`db/`)
- **Utils**: Shared utilities (`utils/`)
- **Tests**: Comprehensive test suite (`tests/`)

---

## 🚀 Before Adding New Features

### 1. Frontend (Next.js/React) - `realestate-broker-ui/`

#### Component Dependencies
- [ ] Check available UI components: `node scripts/validate-components.js`
- [ ] Use existing components when possible
- [ ] Create new components only if necessary
- [ ] Document new components with JSDoc

#### Type Safety
- [ ] Add TypeScript interfaces for new data structures
- [ ] Update existing interfaces if needed
- [ ] Ensure all props are properly typed
- [ ] Add proper error types and responses

#### API Integration
- [ ] Check existing API endpoints in `lib/auth.ts`
- [ ] Follow established patterns for error handling
- [ ] Add proper error types and responses
- [ ] Update API client methods

#### Frontend Integration
- [ ] Check for existing similar components
- [ ] Follow established UI patterns
- [ ] Ensure responsive design
- [ ] Add proper loading and error states
- [ ] Test with different screen sizes

#### Testing
- [ ] Run component validation: `node scripts/validate-components.js`
- [ ] Check TypeScript: `npm run type-check`
- [ ] Run linter: `npm run lint`
- [ ] Run unit tests: `npm run test`
- [ ] Run E2E tests: `npm run test:e2e`
- [ ] Test in browser for visual regressions

---

### 2. Backend (Django) - `backend-django/`

#### Database Changes
- [ ] Create migrations for model changes: `python manage.py makemigrations`
- [ ] Test migrations on clean database: `python manage.py migrate`
- [ ] Add proper indexes and constraints
- [ ] Update serializers for new fields
- [ ] Update admin interface if needed

#### API Development
- [ ] Follow Django REST framework patterns
- [ ] Add proper permissions and authentication
- [ ] Update URL patterns in `urls.py`
- [ ] Add API documentation
- [ ] Handle errors gracefully with proper HTTP status codes

#### Services & Business Logic
- [ ] Create service classes for complex business logic
- [ ] Follow single responsibility principle
- [ ] Add proper logging
- [ ] Handle exceptions appropriately

#### Testing
- [ ] Write unit tests for new functionality
- [ ] Test API endpoints with different scenarios
- [ ] Run Django tests: `python manage.py test`
- [ ] Test with different user permissions

---

### 3. Data Services (Python) - `yad2/`, `gov/`, `mavat/`, `rami/`, `gis/`

#### Service Development
- [ ] Follow established patterns in existing services
- [ ] Add proper error handling and retries
- [ ] Implement rate limiting for external APIs
- [ ] Add comprehensive logging
- [ ] Handle data validation and cleaning

#### MCP Servers
- [ ] Follow MCP protocol standards
- [ ] Add proper error handling
- [ ] Implement proper authentication
- [ ] Add comprehensive documentation
- [ ] Test with MCP clients

#### Data Models
- [ ] Update shared models in `db/models.py` if needed
- [ ] Ensure data consistency across services
- [ ] Add proper validation
- [ ] Consider data migration if schema changes

#### Testing
- [ ] Write unit tests for scrapers and parsers
- [ ] Test with mock data
- [ ] Test error scenarios
- [ ] Run integration tests

---

### 4. Orchestration - `orchestration/`

#### Pipeline Development
- [ ] Follow existing pipeline patterns
- [ ] Add proper error handling and recovery
- [ ] Implement proper scheduling
- [ ] Add monitoring and alerting
- [ ] Ensure data consistency

#### Collectors
- [ ] Follow collector interface standards
- [ ] Add proper error handling
- [ ] Implement retry logic
- [ ] Add data validation
- [ ] Monitor performance

#### Testing
- [ ] Test pipeline components individually
- [ ] Test end-to-end pipeline
- [ ] Test error scenarios
- [ ] Test scheduling and recovery

---

### 5. Database - `db/`

#### Model Changes
- [ ] Update shared models carefully
- [ ] Consider backward compatibility
- [ ] Add proper indexes
- [ ] Update related services
- [ ] Test data migration scripts

#### Testing
- [ ] Test model relationships
- [ ] Test data validation
- [ ] Test migration scripts
- [ ] Test with different database backends

---

### 6. Utils - `utils/`

#### Utility Development
- [ ] Make utilities reusable across services
- [ ] Add proper error handling
- [ ] Add comprehensive documentation
- [ ] Follow Python best practices
- [ ] Add type hints

#### Testing
- [ ] Write unit tests for utilities
- [ ] Test edge cases
- [ ] Test with different inputs
- [ ] Ensure backward compatibility

---

## 🧪 Testing Strategy

### Frontend Testing
```bash
# Component validation
node scripts/validate-components.js

# TypeScript check
cd realestate-broker-ui && npm run type-check

# Linting
cd realestate-broker-ui && npm run lint

# Unit tests
cd realestate-broker-ui && npm run test

# E2E tests
cd realestate-broker-ui && npm run test:e2e
```

### Backend Testing
```bash
# Django tests
cd backend-django && python manage.py test

# Run specific test modules
python manage.py test tests.core.test_models

# Run with coverage
pytest --cov=backend-django/core tests/
```

### Data Services Testing
```bash
# Run all tests
pytest tests/

# Run specific service tests
pytest tests/yad2/
pytest tests/gov/
pytest tests/mavat/
pytest tests/rami/
pytest tests/gis/

# Run integration tests
pytest tests/test_collectors_integration.py
```

### Full System Testing
```bash
# Run all checks
./scripts/pre-commit.sh

# Start all services
./run_all.sh

# Health check
./health-check.sh
```

---

## 🔧 Common Pitfalls to Avoid

### Frontend
1. **Missing UI Components**: Always check what's available before importing
2. **Type Mismatches**: Ensure frontend types match backend serializers
3. **Import Errors**: Use relative paths correctly, check for typos
4. **Missing Dependencies**: Add new dependencies to package.json
5. **State Management**: Don't forget to update state when data changes
6. **Error Boundaries**: Add proper error handling for React components

### Backend
1. **Database Migrations**: Always create migrations for model changes
2. **API Versioning**: Consider API versioning for breaking changes
3. **Authentication**: Don't forget to add proper authentication
4. **Rate Limiting**: Implement rate limiting for external APIs
5. **Error Handling**: Don't forget to handle API errors gracefully
6. **Logging**: Add proper logging for debugging

### Data Services
1. **Rate Limiting**: Implement proper rate limiting for external APIs
2. **Error Handling**: Handle network errors and API failures
3. **Data Validation**: Validate data before processing
4. **Retry Logic**: Implement retry logic for transient failures
5. **Monitoring**: Add monitoring for service health
6. **Data Consistency**: Ensure data consistency across services

### General
1. **Dependencies**: Update requirements.txt files
2. **Documentation**: Update README files and API docs
3. **Environment Variables**: Document new environment variables
4. **Configuration**: Update configuration files
5. **Docker**: Update Dockerfiles if needed
6. **CI/CD**: Update CI/CD pipelines if needed

---

## 🚀 Quick Commands

### Development Setup
```bash
# Install all dependencies
./install-all.sh

# Start all services
./run_all.sh

# Start specific services
cd backend-django && python manage.py runserver
cd realestate-broker-ui && npm run dev
```

### Test Accounts
```bash
# Test accounts with specific plans:
# Admin: admin@example.com / admin123 (Pro Plan - Unlimited assets)
# Demo: demo@example.com / demo123 (Basic Plan - 25 assets)
```

### Testing
```bash
# Run all checks
./scripts/pre-commit.sh

# Frontend tests
cd realestate-broker-ui && npm run test

# Backend tests
cd backend-django && python manage.py test

# Data services tests
pytest tests/
```

### Database
```bash
# Create migrations
cd backend-django && python manage.py makemigrations

# Apply migrations
cd backend-django && python manage.py migrate

# Initialize plan types
cd backend-django && python manage.py init_plans

# Check user plan assignments
cd backend-django && python manage.py shell -c "
from core.models import User
admin = User.objects.get(email='admin@example.com')
demo = User.objects.get(email='demo@example.com')
print(f'Admin: {admin.current_plan.plan_type.name if admin.current_plan else \"No plan\"}')
print(f'Demo: {demo.current_plan.plan_type.name if demo.current_plan else \"No plan\"}')
"
```

### Monitoring
```bash
# Health check
./health-check.sh

# Check logs
docker-compose logs -f

# Monitor specific service
docker-compose logs -f backend-django
```

---

## 📋 Pre-commit Checklist

Before committing any changes:

- [ ] Run `./scripts/pre-commit.sh`
- [ ] All tests pass
- [ ] No linting errors
- [ ] TypeScript compilation successful
- [ ] Database migrations work
- [ ] Documentation updated
- [ ] Environment variables documented
- [ ] Dependencies updated
- [ ] No console.log statements in production code
- [ ] Error handling implemented
- [ ] Logging added where appropriate

---

## 🆘 Troubleshooting

### Common Issues
1. **Import Errors**: Check file paths and dependencies
2. **Type Errors**: Ensure types match between frontend and backend
3. **Database Errors**: Check migrations and model changes
4. **API Errors**: Check authentication and permissions
5. **Test Failures**: Check test data and mocks

### Getting Help
1. Check existing issues in the repository
2. Review the documentation
3. Check the logs for error messages
4. Run tests to identify the issue
5. Ask for help with specific error messages
