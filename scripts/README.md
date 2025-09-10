# Development Scripts

This directory contains scripts to help with development, validation, and maintenance of the Real Estate Agent monorepo.

## 🚀 Quick Start

### Setup Development Environment
```bash
./scripts/setup-dev.sh
```
Sets up the entire development environment with all dependencies.

### Run All Validations
```bash
./scripts/validate-all.sh
```
Comprehensive validation of the entire monorepo.

### Run Pre-commit Checks
```bash
./scripts/pre-commit.sh
```
Essential checks before committing code.

## 📋 Available Scripts

### Setup Scripts

#### `setup-dev.sh`
Complete development environment setup.
- Creates Python virtual environment
- Installs all dependencies
- Sets up database
- Initializes plan types
- Validates configuration

**Usage:**
```bash
./scripts/setup-dev.sh
```

### Validation Scripts

#### `validate-all.sh`
Comprehensive validation of the entire monorepo.
- Frontend validation (TypeScript, linting, tests)
- Backend validation (Django tests, migrations)
- Python services validation
- Data services validation
- Integration tests
- Docker validation
- Environment validation
- Documentation validation

**Usage:**
```bash
./scripts/validate-all.sh
```

#### `validate-service.sh`
Validate a specific service.
- Python syntax checking
- Dependency validation
- Test execution
- Configuration validation

**Usage:**
```bash
./scripts/validate-service.sh <service-name>
```

**Available services:**
- `yad2` - Yad2 real estate scraping
- `gov` - Government data services
- `mavat` - Planning data collection
- `rami` - RAMI planning system
- `gis` - GIS data processing
- `orchestration` - Data pipeline
- `db` - Database models
- `utils` - Shared utilities
- `backend-django` - Django backend
- `realestate-broker-ui` - Frontend

#### `validate-components.js`
Validates UI component imports in the frontend.
- Checks for missing UI components
- Validates import paths
- Prevents component-related errors

**Usage:**
```bash
node scripts/validate-components.js
```

#### `validate-python.py`
Validates Python services across the monorepo.
- Checks import issues
- Validates requirements files
- Checks Django models
- Validates migrations
- Runs linting checks

**Usage:**
```bash
python scripts/validate-python.py
```

#### `pre-commit.sh`
Pre-commit hook to prevent regressions.
- Component validation
- TypeScript compilation
- ESLint checks
- Python services validation
- Django checks

**Usage:**
```bash
./scripts/pre-commit.sh
```

## 🔧 Development Workflow

### 1. Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd realestate-agent

# Setup development environment
./scripts/setup-dev.sh
```

### 2. Before Making Changes
```bash
# Run comprehensive validation
./scripts/validate-all.sh

# Or validate specific service
./scripts/validate-service.sh <service-name>
```

### 3. During Development
```bash
# Run pre-commit checks
./scripts/pre-commit.sh

# Validate components (frontend)
node scripts/validate-components.js

# Validate Python services
python scripts/validate-python.py
```

### 4. Before Committing
```bash
# Run all checks
./scripts/pre-commit.sh

# If you want comprehensive validation
./scripts/validate-all.sh
```

## 🐛 Troubleshooting

### Common Issues

#### "Command not found" errors
- Make sure scripts are executable: `chmod +x scripts/*.sh`
- Check if you're in the project root directory
- Verify required tools are installed (Python, Node.js, etc.)

#### Python import errors
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -e .`
- Check Python path and PYTHONPATH

#### Frontend errors
- Install dependencies: `cd realestate-broker-ui && npm install`
- Check Node.js version (>= 14 recommended)
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

#### Database errors
- Run migrations: `cd backend-django && python manage.py migrate`
- Check database configuration in settings
- Verify database file permissions

### Getting Help

1. **Check the logs**: Look at the output of validation scripts
2. **Review documentation**: Check `DEVELOPMENT_CHECKLIST.md`
3. **Run individual checks**: Use specific validation scripts
4. **Check service health**: Use `./health-check.sh`

## 📚 Related Documentation

- [Development Checklist](../DEVELOPMENT_CHECKLIST.md) - Comprehensive development guide
- [Project README](../README.md) - Project overview
- [API Documentation](../docs/) - API and service documentation

## 🤝 Contributing

When adding new scripts:

1. Follow the naming convention: `validate-<purpose>.sh` or `setup-<purpose>.sh`
2. Add proper error handling and colored output
3. Include usage information in script comments
4. Update this README with script documentation
5. Test scripts on clean environment
6. Add scripts to pre-commit hooks if appropriate

## 📝 Script Development Guidelines

### Bash Scripts
- Use `set -e` to exit on errors
- Add colored output for better UX
- Include usage information
- Handle missing dependencies gracefully
- Return appropriate exit codes

### Python Scripts
- Use type hints where possible
- Add proper error handling
- Include docstrings
- Follow PEP 8 style guide
- Use argparse for command-line arguments

### JavaScript/Node Scripts
- Use modern JavaScript features
- Add proper error handling
- Include JSDoc comments
- Follow ESLint rules
- Use async/await for async operations
