# Real Estate Agent

A comprehensive, organized real estate scraper for Real Estate data with MCP (Model Context Protocol) server integration for seamless LLM use.

## 🎯 Features

- 🏠 **Dynamic Parameter Support**: Search any area with customizable filters (price, location, property type, features)
- 🔍 **Flexible Search**: Support for all known Yad2 parameters (topArea, city, neighborhood, property types, etc.)
- 🤖 **MCP Server Integration**: Connect directly to your LLM for natural language real estate queries
- 📊 **Advanced Analytics**: Price analysis, location breakdowns, property type distributions
- 💾 **Data Export**: Save results to JSON with comprehensive metadata
- 🌐 **Interactive CLI**: User-friendly interface for building searches
- ⚡ **URL Builder**: Generate Yad2 URLs programmatically without scraping
- 🏗️ **Organized Architecture**: Clean, modular codebase with proper separation of concerns

## 📁 Project Structure

```
realestate-agent/
├── yad2/                          # Main package
│   ├── core/                      # Core functionality
│   │   ├── __init__.py
│   │   ├── parameters.py          # Search parameters & validation
│   │   ├── models.py              # Data models (RealEstateListing)
│   │   └── utils.py               # Utility functions
│   ├── scrapers/                  # Web scrapers
│   │   ├── __init__.py
│   │   └── yad2_scraper.py        # Main Yad2 scraper
│   ├── mcp/                       # MCP server for LLM integration
│   │   ├── __init__.py
│   │   └── server.py              # FastMCP server implementation
│   ├── cli/                       # Command-line helpers
│   │   ├── __init__.py
│   │   └── interactive.py         # Interactive CLI utilities
│   ├── tests/                     # Test suite
│   │   ├── __init__.py
│   │   └── test_core.py           # Core functionality tests
│   └── examples/                  # Example scripts & configs
│       ├── __init__.py
│       ├── demo.py                # Demonstration script
│       └── search_config.json     # Example configuration
├── gov/
│   └── mcp/
│       ├── __init__.py
│       └── server.py              # gov.il FastMCP reference server
├── utils/
│   ├── gis.py
│   ├── madlan_scraper.py
│   └── yad2_scraper.py
├── requirements.txt               # Dependencies
├── LICENSE                        # License
└── README.md                      # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd realestate-agent

# Install dependencies
pip install -r requirements.txt
```

### 1.5 Claude Desktop (MCP) setup (optional)

Copy the provided `claude_config.json` to Claude's config location (rename to `claude_desktop_config.json`). Adjust the `command` and `PYTHONPATH` if your Python path differs.

- macOS:

```bash
mkdir -p "${HOME}/Library/Application Support/Claude"
cp claude_config.json "${HOME}/Library/Application Support/Claude/claude_desktop_config.json"
```

- Linux:

```bash
mkdir -p "${HOME}/.config/Claude"
cp claude_config.json "${HOME}/.config/Claude/claude_desktop_config.json"
```

- Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force "$env:APPDATA\Claude" | Out-Null
Copy-Item -Force .\claude_config.json "$env:APPDATA\Claude\claude_desktop_config.json"
```

Then restart Claude Desktop.

### 2. Usage

#### Run Demo (recommended)
```bash
python -m yad2.examples.demo
```

#### Interactive CLI
```bash
python -c "from yad2.cli import InteractiveCLI; InteractiveCLI().main_menu()"
```

#### Run Tests
```bash
python -m yad2.tests.test_core
```

#### Start MCP Server
```bash
python -m yad2.mcp.server
```

#### Programmatic Usage

```python
from yad2 import Yad2Scraper, Yad2SearchParameters

# Create search parameters
params = Yad2SearchParameters(
    maxPrice=8000000,
    city=5000,           # Tel Aviv
    property="1,33",     # Apartments and Penthouses
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
from yad2 import Yad2SearchParameters, Yad2Scraper

params = Yad2SearchParameters(
    city=5000,            # Tel Aviv
    property="1,33",      # Apartments + Penthouses
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
from yad2 import Yad2Scraper

# Your original URL
url = "https://www.yad2.co.il/realestate/forsale?maxPrice=10500000&property=5%2C33%2C39&topArea=2&area=1&city=5000&neighborhood=203"

# Create scraper from URL
scraper = Yad2Scraper.from_url(url)
summary = scraper.get_search_summary()
print(summary)
```

## 🤖 MCP Server for LLM Integration

The MCP server provides seamless integration with LLMs.

### Available Tools

1. `search_real_estate` — Search listings with natural language
2. `get_search_parameters_reference` — Get parameter documentation
3. `analyze_search_results` — Analyze price trends, locations, property types
4. `save_search_results` — Save results to JSON file
5. `build_search_url` — Generate Yad2 URLs without scraping

### Usage with LLM

1. Start the MCP server: `python -m yad2.mcp.server`
2. Configure your LLM to connect to the server
3. Use natural language queries:
   - "Find 4-room apartments in Tel Aviv under 8 million NIS with parking"
   - "Search for penthouses in Jerusalem with elevator"
   - "Analyze the price distribution of the last search"

## 🧪 Testing

Run the core test suite:

```bash
python -m yad2.tests.test_core
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
    "parameters": {"...": "..."},
    "parameter_descriptions": {"...": {"value": "...", "description": "..."}}
  },
  "scrape_time": "2024-01-15T10:30:00",
  "total_listings": 25,
  "listings": [
    {"title": "...", "price": 1234567, "address": "..."}
  ]
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

- **Core**: Parameter handling, data models, utilities (`yad2/core/`)
- **Scrapers**: Web scraping functionality (`yad2/scrapers/`)
- **MCP**: LLM integration server (`yad2/mcp/`)
- **CLI**: Interactive helpers (`yad2/cli/`)
- **Tests**: Core tests (`yad2/tests/`)
- **Examples**: Demo scripts and configurations (`yad2/examples/`)

### Adding New Features

1. Core functionality goes in `yad2/core/`
2. New scrapers go in `yad2/scrapers/`
3. MCP tools go in `yad2/mcp/server.py`
4. CLI features go in `yad2/cli/`
5. Add tests in `yad2/tests/`

### Entry Points

- Run Demo: `python -m yad2.examples.demo`
- Start MCP server: `python -m yad2.mcp.server`
- Run tests: `python -m yad2.tests.test_core`
- Interactive CLI: `python -c "from yad2.cli import InteractiveCLI; InteractiveCLI().main_menu()"`

## 🚨 Troubleshooting

### Common Issues

1. **Import errors**: Ensure you ran `pip install -r requirements.txt` and `cd realestate-agent`
2. **No listings found**: Check if parameters are too restrictive
3. **Rate limiting**: Increase delay between requests
4. **Parsing errors**: Yad2 may have changed their HTML structure

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 What's New in v1.0

- ✅ **Organized Architecture**: Clean, modular codebase
- ✅ **Consolidated Functionality**: No duplicated code
- ✅ **Enhanced MCP Server**: Updated with dynamic parameter specifications
- ✅ **Core Test Suite**: Easy to run via module
- ✅ **Improved Examples**: Run with `python -m`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite: `python -m yad2.tests.test_core`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Always respect the website's terms of service and rate limits. The authors are not responsible for any misuse of this software.

---

**Ready to search real estate with natural language through your LLM! 🏠🤖**