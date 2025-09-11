# Yad2 MCP Server

Enhanced Model Context Protocol (MCP) server for comprehensive Yad2 real estate integration with LLMs.

## Overview

This MCP server provides comprehensive access to Yad2 real estate data, including property types, location services, market analysis, and advanced search capabilities. It's designed to work seamlessly with LLMs for intelligent real estate search and analysis.

## Features

### 🏠 Core Search Functionality
- **search_real_estate**: Advanced property search with filters
- **build_search_url**: Generate search URLs with parameters
- **get_search_parameters_reference**: Complete parameter reference
- **analyze_search_results**: Detailed result analysis
- **save_search_results**: Export results to JSON

### 🏘️ Property Types Management
- **get_all_property_types**: Complete property type catalog
- **get_property_type_details**: Detailed property information
- **convert_property_type**: Format conversion (code/Hebrew/English)
- **get_property_type_recommendations**: AI-powered recommendations
- **compare_property_types**: Side-by-side comparison
- **validate_property_type_code**: Code validation
- **export_property_types**: Export to JSON/CSV/Excel

### 📍 Location Services
- **search_locations**: Autocomplete location search
- **get_location_codes**: All location codes and names
- **get_city_info**: City information by ID

### 📊 Analysis & Statistics
- **get_property_type_statistics**: Comprehensive statistics
- **get_market_analysis**: Market position and trends
- **get_comparison_table**: Property type comparison matrix

### 🔍 Advanced Search
- **search_with_property_type**: Search by property name
- **get_search_recommendations**: Intelligent suggestions

### ⚙️ Bulk Operations
- **bulk_property_type_operations**: Mass operations
- **get_api_status**: System status check
- **test_property_type_functionality**: Comprehensive testing

### 📚 Help & Documentation
- **get_property_types_help**: Complete documentation
- **get_property_types_faq**: Frequently asked questions
- **get_troubleshooting_guide**: Problem solving guide
- **print_property_types_summary**: Formatted overview

## Installation & Setup

### Dependencies
```bash
pip install requests beautifulsoup4 lxml pandas openpyxl fastmcp
```

### Running the Server
```bash
cd yad2/mcp
python server.py
```

## Usage Examples

### Basic Property Search
```python
# Search for apartments in Tel Aviv under 5M NIS
result = await search_real_estate(
    property="1",  # Apartment code
    maxPrice=5000000,
    city="5000",   # Tel Aviv city code
    max_pages=3
)
```

### Property Type Operations
```python
# Get all property types
all_types = await get_all_property_types()

# Get detailed information
details = await get_property_type_details(property_code=1)

# Convert to English
english_name = await convert_property_type(
    value="1", 
    from_format="yad2", 
    to_format="english"
)
```

### Location Services
```python
# Search for locations
locations = await search_locations(search_text="רמת גן")

# Get city information
city_info = await get_city_info(city_id="8600")
```

### Market Analysis
```python
# Get property recommendations
recommendations = await get_property_type_recommendations(
    budget=3000000,
    family_size=4,
    location="תל אביב",
    investment=True
)

# Get market trends
trends = await get_property_type_trends()

# Compare property types
comparison = await compare_property_types(type1="1", type2="5")
```

### Advanced Search
```python
# Search using property type name instead of code
results = await search_with_property_type(
    property_type_name="דירה",
    maxPrice=4000000,
    location="רמת גן"
)

# Get intelligent search recommendations
suggestions = await get_search_recommendations(
    budget=2500000,
    family_size=3,
    location="תל אביב"
)
```

## Property Type Codes

| Code | Hebrew Name | English Name | Category |
|------|-------------|--------------|----------|
| 1 | דירה | Apartment | Residential |
| 3 | דירה עם גינה | Apartment with Garden | Residential |
| 5 | וילה | Villa | Residential |
| 6 | נטהאוס | Penthouse | Residential |
| 15 | בניין | Building | Commercial |
| 33 | קרקע | Land | Land |
| 31 | לופט | Loft | Residential |
| 32 | טריפלקס | Triplex | Residential |
| 34 | דירת גן | Garden Apartment | Residential |
| 35 | גג | Rooftop | Residential |
| 36 | יחידה | Unit | Residential |
| 37 | מיני פנטהאוס | Mini Penthouse | Residential |
| 39 | בית | House | Residential |

## API Response Format

All endpoints return responses in this format:
```json
{
  "success": true/false,
  "data": {}, // Response data
  "error": "Error message if failed"
}
```

## Testing

```python
# Run comprehensive functionality tests
test_results = await test_property_type_functionality()

# Check API status
status = await get_api_status()
```

## Error Handling

The server includes comprehensive error handling:
- Input validation
- API timeout management
- Graceful degradation
- Detailed error messages
- Retry logic for transient failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For help and troubleshooting:
```python
# Get help documentation
help_info = await get_property_types_help()

# Get FAQ
faq = await get_property_types_faq()

# Get troubleshooting guide
troubleshooting = await get_troubleshooting_guide()
```

## License

This project is licensed under the MIT License.
