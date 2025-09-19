# Nadlan.gov.il E2E Tests

This directory contains comprehensive end-to-end tests for the integration with nadlan.gov.il, including transaction data collection, price analysis, and comparison functionality.

## Overview

The Nadlan integration provides real estate transaction data from the Israeli government's official real estate database. This data is used for:

- **Transaction History**: Historical sales data for properties
- **Price Analysis**: Average, minimum, maximum prices by location
- **Market Comparison**: Comparing prices across different areas
- **Data Validation**: Ensuring data quality and structure

## Test Files

### 1. `test_nadlan_integration.py`
Core integration tests for Nadlan functionality:
- Basic scraper functionality
- GovCollector integration
- Pipeline integration
- Transaction price analysis

### 2. `test_transaction_comparison.py`
Advanced tests for transaction comparison:
- Multi-address data collection
- Price analysis and comparison
- Transaction structure validation
- Filtering and sorting functionality

### 3. `test_collectors_integration.py` (Updated)
Updated collector tests including:
- Nadlan scraper tests
- GovCollector with Nadlan integration
- All other collectors

### 4. `test_pipeline_optimized_e2e.py` (Updated)
Updated pipeline tests including:
- Individual collectors with Nadlan
- Data quality validation
- Transaction comparison functionality

## Running the Tests

### Quick Start
```bash
# Run all Nadlan E2E tests
./scripts/test-nadlan-e2e.sh
```

### Individual Test Files
```bash
# Run specific test files
python -m pytest tests/e2e/test_nadlan_integration.py -v
python -m pytest tests/e2e/test_transaction_comparison.py -v
python -m pytest tests/e2e/test_collectors_integration.py -m "nadlan" -v
python -m pytest tests/e2e/test_pipeline_optimized_e2e.py -k "nadlan" -v
```

### Specific Test Categories
```bash
# Run only integration tests
python -m pytest tests/e2e/ -m "nadlan and integration" -v

# Run only external service tests
python -m pytest tests/e2e/ -m "nadlan and external_service" -v

# Run only slow tests
python -m pytest tests/e2e/ -m "nadlan and slow" -v
```

## Test Configuration

### Environment Variables
```bash
export HEADLESS=true          # Run browser in headless mode
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

### Test Addresses
The tests use these default addresses:
- `רוזוב 14 תל אביב` (Ruzov 14 Tel Aviv)
- `רוטשילד 1 תל אביב` (Rothschild 1 Tel Aviv)
- `דיזנגוף 50 תל אביב` (Dizengoff 50 Tel Aviv)

### Timeouts and Retries
- **Timeout**: 60 seconds for browser operations
- **Retries**: 3 attempts for each operation
- **Delays**: 5 seconds between retry attempts

## Test Features

### 1. Data Collection
- **Address Search**: Search for addresses using Nadlan's autocomplete
- **Transaction Fetching**: Retrieve historical transaction data
- **Neighborhood Info**: Get neighborhood information and IDs

### 2. Price Analysis
- **Statistical Analysis**: Average, minimum, maximum prices
- **Price Range**: Calculate price variance and distribution
- **Comparison**: Compare prices across different locations

### 3. Data Validation
- **Structure Validation**: Ensure proper data structure
- **Type Checking**: Validate data types (strings, numbers, dates)
- **Range Validation**: Check for reasonable price ranges

### 4. Pipeline Integration
- **Collector Integration**: Test GovCollector with Nadlan
- **Pipeline Execution**: Test full data pipeline
- **Result Analysis**: Analyze pipeline results by source

## Expected Results

### Successful Test Run
```
✅ Nadlan Integration Tests
✅ Nadlan Collector Tests
✅ Pipeline Tests with Nadlan
✅ Transaction Comparison Tests
```

### Sample Output
```
📊 Price analysis:
   Average: ₪2,500,000
   Minimum: ₪1,800,000
   Maximum: ₪3,200,000
   Range: ₪1,400,000

🔍 Comparing prices across addresses:
   Lowest average: ₪2,100,000
   Highest average: ₪2,800,000
   Variance: ₪700,000
```

## Troubleshooting

### Common Issues

1. **No Transactions Found**
   - Check internet connection
   - Verify Nadlan website accessibility
   - Try different test addresses

2. **Browser Issues**
   - Ensure Chrome/Chromium is installed
   - Check WebDriver compatibility
   - Try running with `--headed` flag

3. **Timeout Errors**
   - Increase timeout values
   - Check network stability
   - Verify test addresses are valid

### Debug Mode
```bash
# Run with browser visible
python -m pytest tests/e2e/test_nadlan_integration.py -v --headed

# Run with detailed logging
python -m pytest tests/e2e/test_nadlan_integration.py -v -s --log-cli-level=DEBUG
```

## Dependencies

### Required Packages
```
selenium>=4.0.0
webdriver-manager>=3.8.0
beautifulsoup4>=4.9.0
requests>=2.25.0
pytest>=6.0.0
```

### Browser Requirements
- Chrome or Chromium browser
- ChromeDriver (managed by webdriver-manager)

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Nadlan E2E Tests
  run: |
    chmod +x scripts/test-nadlan-e2e.sh
    ./scripts/test-nadlan-e2e.sh
```

### Docker
```dockerfile
# Install Chrome for headless testing
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*
```

## Performance Considerations

### Test Duration
- **Individual Tests**: 30-60 seconds each
- **Full Suite**: 5-10 minutes
- **CI Environment**: May take longer due to network latency

### Resource Usage
- **Memory**: ~200MB per test
- **CPU**: Moderate usage during browser operations
- **Network**: Moderate data usage for web scraping

## Contributing

### Adding New Tests
1. Follow the existing test structure
2. Use appropriate pytest markers
3. Include retry logic for external services
4. Add proper logging and assertions

### Test Data
- Use realistic test addresses
- Include edge cases and error scenarios
- Validate data quality and structure

### Documentation
- Update this README for new features
- Include sample outputs
- Document any new dependencies
