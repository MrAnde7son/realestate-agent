# Yad2 Real Estate Scraper & MCP Server

A comprehensive, organized real estate scraper for Yad2.co.il with MCP (Model Context Protocol) server integration for seamless LLM use.

## 🎯 Features

- 🏠 **Dynamic Parameter Support**: Search any area with customizable filters (price, location, property type, features)
- 🔍 **Flexible Search**: Support for all known Yad2 parameters (topArea, city, neighborhood, property types, etc.)
- 🤖 **MCP Server Integration**: Connect directly to your LLM for natural language real estate queries
- 📊 **Advanced Analytics**: Price analysis, location breakdowns, property type distributions
- 💾 **Data Export**: Save results to JSON with comprehensive metadata
- 🌐 **Interactive CLI**: User-friendly command-line interface for building searches
- ⚡ **URL Builder**: Generate Yad2 URLs programmatically without scraping
- 🏗️ **Organized Architecture**: Clean, modular codebase with proper separation of concerns

## 📁 Project Structure

```
yad2/
├── yad2_scraper/                    # Main package
│   ├── core/                        # Core functionality
│   │   ├── __init__.py
│   │   ├── parameters.py            # Search parameters & validation
│   │   ├── models.py                # Data models (RealEstateListing)
│   │   └── utils.py                 # Utility functions
│   ├── scrapers/                    # Web scrapers
│   │   ├── __init__.py
│   │   └── yad2_scraper.py         # Main Yad2 scraper
│   ├── mcp/                         # MCP server for LLM integration
│   │   ├── __init__.py
│   │   └── server.py               # MCP server implementation
│   ├── cli/                         # Command-line interface
│   │   ├── __init__.py
│   │   └── interactive.py          # Interactive CLI
│   ├── tests/                       # Test suite
│   │   ├── __init__.py
│   │   └── test_core.py            # Core functionality tests
│   ├── examples/                    # Example scripts & configs
│   │   ├── __init__.py
│   │   ├── demo.py                 # Demonstration script
│   │   └── search_config.json      # Example configuration
│   └── __init__.py                 # Package exports
├── run_cli.py                      # CLI entry point
├── run_mcp_server.py              # MCP server entry point
├── run_tests.py                   # Test runner entry point
├── requirements.txt               # Dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd yad2

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Usage

#### Interactive CLI
```bash
python run_cli.py
```

#### Run Tests
```bash
python run_tests.py
```

#### Start MCP Server
```bash
python run_mcp_server.py
```

#### Programmatic Usage
```python
from yad2_scraper import Yad2Scraper, Yad2SearchParameters

# Create search parameters
params = Yad2SearchParameters(
    maxPrice=8000000,
    city=5000,  # Tel Aviv
    property="1,33",  # Apartments and Penthouses
    rooms="3-4",
    elevator=1,
    parking=1
)

# Create scraper and search
scraper = Yad2Scraper(params)
listings = scraper.scrape_all_pages(max_pages=3)

# Save results
scraper.save_to_json("my_search.json")
```

## 🔧 Search Parameters

### Location Parameters
- `topArea`: Regional area
  - 1: North
  - 2: Center
  - 3: South
  - 4: Jerusalem Area
  - 5: West Bank
- `area`: Sub-area within region (1=TLV, 3=RamatGan,Givataim)
- `city`: City ID (5000=Tel Aviv, 6200=Jerusalem, 6300=Haifa)
- `neighborhood`: Neighborhood ID (203=Ramat HaHayal, 199=City Center, etc.)

### Price Parameters
- `maxPrice`: Maximum price in NIS
- `minPrice`: Minimum price in NIS

### Property Parameters
- `property`: Property types (comma-separated)
  - 1: Apartment
  - 2: House/Villa
  - 5: Duplex
  - 33: Penthouse
  - 39: Studio
- `rooms`: Number of rooms (e.g., "3-4", "4+")
- `size`: Property size range
- `floor`: Floor range

### Features
- `parking`: Number of parking spaces required
- `elevator`: Requires elevator (1=yes, 0=no)
- `balcony`: Requires balcony (1=yes, 0=no)
- `renovated`: Must be renovated (1=yes, 0=no)
- `airCondition`: Has air conditioning (1=yes, 0=no)
- `mamad`: Has safe room (1=yes, 0=no)

## 📚 Usage Examples

### Example 1: Tel Aviv Luxury Apartments
```python
from yad2_scraper import Yad2SearchParameters, Yad2Scraper

params = Yad2SearchParameters(
    city=5000,           # Tel Aviv
    property="1,33",     # Apartments + Penthouses
    minPrice=5000000,
    maxPrice=15000000,
    rooms="4+",
    elevator=1,
    parking=2
)

scraper = Yad2Scraper(params)
listings = scraper.scrape_all_pages(max_pages=2)
```

### Example 2: Jerusalem Family Homes
```python
params = Yad2SearchParameters(
    topArea=4,           # Jerusalem area
    property="1,2,5",    # Apartments + Houses + Duplexes
    maxPrice=8000000,
    rooms="4-5",
    balcony=1
)
```

### Example 3: Extract from Existing URL
```python
from yad2_scraper import Yad2Scraper

# Your original URL
url = "https://www.yad2.co.il/realestate/forsale?maxPrice=10500000&property=5%2C33%2C39&topArea=2&area=1&city=5000&neighborhood=203"

# Create scraper from URL
scraper = Yad2Scraper.from_url(url)
summary = scraper.get_search_summary()
print(summary)
```

## 🤖 MCP Server for LLM Integration

The MCP server provides seamless integration with LLMs like Claude, GPT-4, etc.

### Available Tools

1. **search_real_estate** - Search listings with natural language
2. **get_search_parameters_reference** - Get parameter documentation
3. **analyze_search_results** - Analyze price trends, locations, property types
4. **save_search_results** - Save results to JSON file
5. **build_search_url** - Generate Yad2 URLs without scraping

### Usage with LLM

1. Start the MCP server: `python run_mcp_server.py`
2. Configure your LLM to connect to the server
3. Use natural language queries:
   - "Find 4-room apartments in Tel Aviv under 8 million NIS with parking"
   - "Search for penthouses in Jerusalem with elevator"
   - "Analyze the price distribution of the last search"

## 🧪 Testing

Run the comprehensive test suite:

```bash
python run_tests.py
```

Tests cover:
- Parameter system validation
- URL building and parsing
- Data model functionality
- Utility functions

## 📊 Data Export Format

Results are saved in JSON format with:
- Search metadata (parameters, URL, timestamp)
- Individual listing details (price, address, features, images)
- Search summary and statistics

Example output:
```json
{
  "search_summary": {
    "search_url": "https://www.yad2.co.il/realestate/forsale?...",
    "parameters": {...},
    "parameter_descriptions": {...}
  },
  "scrape_time": "2024-01-15T10:30:00",
  "total_listings": 25,
  "listings": [...]
}
```

## 🛡️ Rate Limiting & Ethics

- Built-in delays between requests (respectful scraping)
- Retry logic for failed requests
- User-agent rotation support
- Follows robots.txt guidelines
- Configurable request delays

## 🔧 Development

### Project Organization

The codebase is organized into logical modules:

- **Core**: Parameter handling, data models, utilities
- **Scrapers**: Web scraping functionality
- **MCP**: LLM integration server
- **CLI**: Interactive command-line interface
- **Tests**: Comprehensive test suite
- **Examples**: Demo scripts and configurations

### Adding New Features

1. Core functionality goes in `yad2_scraper/core/`
2. New scrapers go in `yad2_scraper/scrapers/`
3. MCP tools go in `yad2_scraper/mcp/server.py`
4. CLI features go in `yad2_scraper/cli/`
5. Add tests in `yad2_scraper/tests/`

### Entry Points

- `run_cli.py` - Interactive command-line interface
- `run_mcp_server.py` - MCP server for LLM integration  
- `run_tests.py` - Test suite runner

## 🚨 Troubleshooting

### Common Issues

1. **Import errors**: Run `python run_tests.py` to verify installation
2. **No listings found**: Check if parameters are too restrictive
3. **Rate limiting**: Increase delay between requests
4. **Parsing errors**: Yad2 may have changed their HTML structure

### Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 What's New in v1.0

- ✅ **Organized Architecture**: Clean, modular codebase
- ✅ **Consolidated Functionality**: No duplicated code
- ✅ **Enhanced MCP Server**: Updated with user's parameter specifications
- ✅ **Comprehensive Testing**: Full test suite
- ✅ **Better CLI**: Improved interactive interface
- ✅ **Proper Documentation**: Complete API reference

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite: `python run_tests.py`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Always respect the website's terms of service and rate limits. The authors are not responsible for any misuse of this software.

---

**Ready to search real estate with natural language through your LLM! 🏠🤖**