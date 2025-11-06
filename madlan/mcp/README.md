# Madlan MCP Server

Model Context Protocol (MCP) server for comprehensive Madlan real estate integration with LLMs.

## Overview

This MCP server provides comprehensive access to Madlan real estate data through their GraphQL API, including address autocomplete, property search, and listing retrieval. It's designed to work seamlessly with LLMs for intelligent real estate search and analysis.

## Features

### 🏠 Core Search Functionality
- **search_real_estate**: Advanced property search with filters
- **fetch_listings**: Fetch listings by location document ID
- **get_addresses**: Autocomplete addresses and get address details

### 📍 Location Services
- **get_addresses**: Autocomplete location search with detailed address information
- Address hierarchy and document ID retrieval

### 🔍 Advanced Search
- Support for both "unitBuy" (for sale) and "unitRent" (for rent) listings
- Price range filtering
- Rooms, area, floor, and bathroom range filtering
- Building class, condition, and seller type filters
- Amenities filtering
- Commercial real estate support

## Installation & Setup

### Dependencies
```bash
pip install requests fastmcp
```

### Running the Server
```bash
cd madlan/mcp
python server.py
```

## Usage Examples

### Basic Address Search
```python
# Search for addresses
result = await get_addresses(text="רוזוב 14 תל")

# Use the docId from the result for property search
location_doc_id = result["addresses"][0]["docId"]
```

### Property Search
```python
# Search for properties for sale
result = await search_real_estate(
    location_doc_id="רוזוב-14-תל-אביב-יפו-ישראל",
    deal_type="unitBuy",
    price_range=[1000000, 5000000],
    rooms_range=[3, 5],
    limit=50
)

# Search for rental properties
result = await search_real_estate(
    location_doc_id="רוזוב-14-תל-אביב-יפו-ישראל",
    deal_type="unitRent",
    price_range=[5000, 15000],
    rooms_range=[2, 4],
    limit=50
)
```

### Fetch Listings
```python
# Fetch listings with simplified parameters
result = await fetch_listings(
    location_doc_id="רוזוב-14-תל-אביב-יפו-ישראל",
    deal_type="unitBuy",
    price_range=[2000000, 4000000],
    rooms_range=[3, 4],
    limit=20
)
```

## Deal Types

- **unitBuy**: Properties for sale
- **unitRent**: Properties for rent

## Search Parameters

### Location
- `location_doc_id`: Document ID from address autocomplete (required for location-based search)

### Price & Size
- `price_range`: [min, max] price range in NIS
- `rooms_range`: [min, max] number of rooms
- `area_range`: [min, max] area in square meters
- `floor_range`: [min, max] floor number
- `baths_range`: [min, max] number of bathrooms

### Filters
- `building_class`: List of building class filters
- `general_condition`: List of general condition filters
- `seller_type`: List of seller type filters
- `amenities`: Dictionary of amenity filters
- `no_fee`: Filter for no fee listings
- `price_drop`: Filter for listings with price drops
- `under_price_estimation`: Filter for listings under price estimation
- `discounted_projects`: Filter for discounted projects
- `only_immediate`: Filter for immediate availability only
- `is_commercial_real_estate`: Filter for commercial real estate

### Pagination
- `limit`: Maximum number of results (default: 50)
- `offset`: Offset for pagination (default: 0)

## API Response Format

All endpoints return responses in this format:
```json
{
  "success": true/false,
  "total_listings": 0,
  "listings": [],
  "error": "Error message if failed"
}
```

## Error Handling

The server includes comprehensive error handling:
- Input validation
- API timeout management
- Graceful degradation
- Detailed error messages
- Automatic token management

## Authentication

The server automatically handles authentication by fetching user tokens from the Madlan homepage. No manual token configuration is required.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License.

