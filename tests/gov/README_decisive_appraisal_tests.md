# Decisive Appraisal Tests

This document describes the comprehensive test suite for the decisive appraisal functionality in the `gov.mcp.decisive` module.

## Overview

The decisive appraisal system fetches and parses building appraisal decisions (הכרעת שמאי מייעץ) from the Israeli government website (gov.il). The system:

1. Queries the dynamic collector for appraisal decisions
2. Parses HTML responses to extract key information
3. Handles various text formats and separators
4. Provides structured data for further processing

## Test Coverage

### 1. Field Extraction Tests

- **`test_extract_field_success`**: Tests successful extraction of date, appraiser, and committee fields
- **`test_extract_field_not_found`**: Tests behavior when a field is not present
- **`test_extract_field_with_different_separators`**: Tests extraction with various separators (|, -, ,)
- **`test_extract_field_at_end`**: Tests extraction when field is at the end of text

### 2. HTML Parsing Tests

- **`test_parse_items_success`**: Tests successful parsing of HTML with multiple items
- **`test_parse_items_no_links`**: Tests parsing when items don't have PDF links
- **`test_parse_items_empty`**: Tests parsing of empty HTML
- **`test_parse_items_malformed`**: Tests parsing of malformed HTML

### 3. API Integration Tests

- **`test_fetch_decisive_appraisals_success`**: Tests successful API calls
- **`test_fetch_decisive_appraisals_multiple_pages`**: Tests pagination across multiple pages
- **`test_fetch_decisive_appraisals_no_results`**: Tests behavior when no results are found
- **`test_fetch_decisive_appraisals_with_parameters`**: Tests filtering by block and plot
- **`test_fetch_decisive_appraisals_http_error`**: Tests HTTP error handling
- **`test_fetch_decisive_appraisals_connection_error`**: Tests network error handling

### 4. Real Data Integration Tests

- **`test_decisive_appraisal_with_real_pdf_data`**: Uses the actual PDF file to verify parsing logic
- **`test_decisive_appraisal_hebrew_text_parsing`**: Tests various Hebrew text formats and edge cases

### 5. MCP Server Tests

- **`test_decisive_appraisal_tool`**: Tests the MCP server integration

## Test Data

The tests use the following real data from the uploaded PDF:

- **Document Type**: הכרעת שמאי מייעץ (Decisive Appraiser Advisory)
- **Date**: 20-07-2025
- **Block (גוש)**: 2189
- **Plot (חלקה)**: 85
- **Appraiser**: גולדברג ארנון (Goldberg Arnon)
- **Committee**: ועדה מקומית אשדוד (Local Committee Ashdod)
- **Subject**: היטל השבחה (Betterment Levy)

## Key Test Patterns

### Mocking Strategy

Tests use `unittest.mock.patch` to mock:
- HTTP requests to the gov.il API
- HTML responses with various data structures
- Network errors and HTTP status codes

### Text Parsing Validation

Tests verify:
- Field extraction with different separators
- Hebrew text handling
- Edge cases and error conditions
- Proper text formatting and structure

### HTML Structure Testing

Tests cover:
- Items with and without PDF links
- Various HTML structures
- Malformed HTML handling
- Empty response handling

## Running the Tests

```bash
# Run all decisive appraisal tests
python3 -m pytest tests/gov/test_decisive_appraisal.py -v

# Run specific test categories
python3 -m pytest tests/gov/test_decisive_appraisal.py -k "extract_field" -v
python3 -m pytest tests/gov/test_decisive_appraisal.py -k "parse_items" -v
python3 -m pytest tests/gov/test_decisive_appraisal.py -k "fetch_decisive_appraisals" -v

# Run specific tests
python3 -m pytest tests/gov/test_decisive_appraisal.py::test_extract_field_success -v
```

## Demo Script

A demonstration script is included at `tests/gov/test_decisive_appraisal_demo.py` that shows:

- Field extraction from various text formats
- HTML parsing simulation with real data
- Edge case handling
- Integration with the decisive module

Run with:
```bash
python3 tests/gov/test_decisive_appraisal_demo.py
```

## Test Results

All 17 tests pass successfully, providing comprehensive coverage of:

- ✅ Field extraction functionality
- ✅ HTML parsing capabilities
- ✅ API integration
- ✅ Error handling
- ✅ Real data integration
- ✅ Hebrew text processing
- ✅ Edge case scenarios

## Key Features Tested

### Robust Field Extraction

The `_extract_field` function handles:
- Multiple separator types (|, -, ,)
- Hebrew text with various formats
- Field boundaries and edge cases
- Missing or malformed data

### HTML Parsing

The `_parse_items` function processes:
- Items with PDF links
- Items without links
- Various HTML structures
- Proper text formatting with separators

### API Integration

The `fetch_decisive_appraisals` function manages:
- HTTP requests and responses
- Pagination across multiple pages
- Error handling and retries
- Parameter filtering

## Dependencies

Tests require:
- `pytest` for test framework
- `requests` for HTTP mocking
- `beautifulsoup4` for HTML parsing
- `unittest.mock` for mocking functionality
- `fastmcp` for MCP server testing

## Integration with Real PDF Data

The test suite includes a specific test that uses the actual PDF file:
`הכרעת שמאי מייעץ מיום 20-07-2025 בעניין היטל השבחה קי.בי.עי קבוצת בוני ערים  נ ועדה מקומית אשדוד ג 2189 ח 85 - גולדברג ארנון.pdf`

This ensures that:
- The parsing logic works with real-world data
- Hebrew text is handled correctly
- Field extraction works with actual document content
- The system can process real appraisal decisions

## Future Enhancements

Potential areas for additional testing:
- PDF content extraction and parsing
- More complex HTML structures
- Additional field types and formats
- Performance testing with large datasets
- Integration testing with external APIs
