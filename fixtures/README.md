# Test Fixtures & Sample Data

This directory contains synthetic data and expected outputs for testing the Nadlaner™ platform components.

## Files Overview

### `synthetic_assets.json`
Synthetic real estate assets representing different property types and scenarios:
- **Asset 001**: 4-room apartment in Ramat HaHayal, Tel Aviv
- **Asset 002**: 3-room apartment in Dizengoff, Tel Aviv  
- **Asset 003**: Penthouse in Rothschild, Tel Aviv
- **Asset 004**: Neighborhood-level analysis for Ramat HaHayal
- **Asset 005**: Parcel-level analysis for Dizengoff area

### `source_records.json`
Source records showing data provenance and raw data from external sources:
- **Yad2 Data**: Property listings with photos, features, agent info
- **GIS Permits**: Building permit information with PDFs
- **GIS Rights**: Land use and building rights data
- **Nadlan Transactions**: Comparable transaction data
- **RAMI Plans**: Planning document information
- **Mavat Plans**: National planning portal data

### `expected_outputs.json`
Gold file tests for scrapers and parsers with expected outputs:
- **Yad2 Scraper**: Expected listing data structure
- **GIS Services**: Geocoding, permits, land use data
- **Nadlan Scraper**: Transaction data format
- **RAMI API**: Planning document responses
- **Mavat API**: Plan search results
- **GovMap API**: Parcel lookup data
- **Integration Tests**: Complete pipeline outputs

## Usage

### For Unit Testing
```python
import json

# Load synthetic assets
with open('fixtures/synthetic_assets.json', 'r') as f:
    assets = json.load(f)

# Use in tests
def test_asset_creation():
    asset_data = assets['assets'][0]
    # Test asset creation logic
```

### For Integration Testing
```python
# Load expected outputs
with open('fixtures/expected_outputs.json', 'r') as f:
    expected = json.load(f)

# Test scraper output
def test_yad2_scraper():
    result = yad2_scraper.scrape(test_url)
    expected_output = expected['test_cases']['yad2_scraper']['expected_output']
    assert result == expected_output
```

### For Development
```python
# Load source records for data lineage testing
with open('fixtures/source_records.json', 'r') as f:
    source_records = json.load(f)

# Test data promotion logic
def test_promote_raw_to_asset():
    source_record = source_records['source_records'][0]
    asset = Asset()
    promote_raw_to_asset(asset, source_record['raw'])
    # Verify field mapping
```

## Data Quality Standards

### Completeness
- All required fields populated
- Realistic data ranges
- Consistent data types
- Proper Hebrew/English formatting

### Accuracy
- Valid coordinates (EPSG:2039)
- Realistic property prices
- Consistent address formats
- Valid date formats (ISO 8601)

### Consistency
- Cross-reference data between sources
- Consistent field naming
- Proper data relationships
- Valid foreign key references

## Test Scenarios

### Basic Property Analysis
- Single property with complete data
- All sources providing data
- High confidence scores
- No missing fields

### Partial Data Collection
- Some sources failing
- Missing optional fields
- Lower confidence scores
- Graceful degradation

### Data Conflicts
- Conflicting data from sources
- Priority resolution
- Data quality assessment
- Conflict resolution

### Edge Cases
- Invalid addresses
- Missing coordinates
- Empty search results
- API failures

## Maintenance

### Regular Updates
- Update synthetic data quarterly
- Refresh expected outputs after API changes
- Add new test scenarios as features develop
- Maintain data quality standards

### Version Control
- Track changes to fixtures
- Document data source updates
- Maintain backward compatibility
- Version fixture files

### Validation
- Validate JSON syntax
- Check data consistency
- Verify realistic values
- Test with actual scrapers

## Contributing

When adding new fixtures:

1. **Follow Naming Conventions**: Use descriptive, consistent names
2. **Maintain Data Quality**: Ensure realistic, consistent data
3. **Document Changes**: Update this README with new fixtures
4. **Test Thoroughly**: Verify fixtures work with actual code
5. **Version Control**: Commit changes with clear messages

## Related Documentation

- [Data Lineage Documentation](../docs/DATA_LINEAGE.md)
- [MCP Tools Catalog](../docs/MCP_TOOLS.md)
- [Architecture Overview](../docs/ARCHITECTURE.md)
- [Testing Guidelines](../tests/README.md)
