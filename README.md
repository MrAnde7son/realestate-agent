# Real Estate Agent

A comprehensive real estate intelligence platform with MCP (Model Context Protocol) server integration for seamless LLM use. Includes Israeli real estate scraping, planning document access (RAMI), and Tel Aviv GIS integration.

## 🎯 Features

### 🏠 Real Estate Intelligence
- 🏠 **Dynamic Parameter Support**: Search any area with customizable filters (price, location, property type, features)
- 🔍 **Flexible Search**: Support for all known Yad2 parameters (topArea, city, neighborhood, property types, etc.)
- 📊 **Advanced Analytics**: Price analysis, location breakdowns, property type distributions
- 💾 **Data Export**: Save results to JSON with comprehensive metadata
- 📣 **Alert Notifications**: Email or WhatsApp alerts when listings match criteria
- 📄 **Property Documents**: Attach land registry extracts and condo plans manually, while permits and rights documents are collected automatically for each listing

### 🏛️ Planning & Government Data (RAMI)
- 📄 **Israeli Planning Documents**: Access land.gov.il TabaSearch API for planning data
- 🗂️ **Document Downloads**: Automatic download of regulations (תקנון), blueprints (תשריט), appendices (נספח), and archives (ממ"ג)
- 🔍 **Smart Search**: Search by plan number, city, gush/chelka, or multiple criteria
- 🇮🇱 **Tel Aviv Optimized**: Pre-configured searches for Tel Aviv metropolitan area

### 🗺️ GIS & Location Intelligence
- 📍 **Address Geocoding**: Convert addresses to coordinates (EPSG:2039)
- 🏗️ **Building Permits**: Find nearby construction permits with PDF downloads
- 🌍 **Spatial Analysis**: Land use, zoning, parcels, and neighborhood data
- 🔒 **Safety Data**: Dangerous buildings, preservation status, noise levels

### 🤖 LLM Integration
- 🤖 **Multiple MCP Servers**: Yad2, RAMI, GIS, and gov.il data access
- 🌐 **Natural Language Queries**: Ask questions in plain language
- ⚡ **URL Builder**: Generate search URLs programmatically without scraping
- 🔧 **Development Tools**: Robust testing and debugging capabilities

### 💻 User Interfaces
- 🌐 **Interactive CLI**: User-friendly interface for building searches
- 🖥️ **Broker Dashboard UI**: Next.js interface for managing listings, alerts, and mortgage analysis
- 🏗️ **Organized Architecture**: Clean, modular codebase with proper separation of concerns

## 📁 Project Structure

```
realestate-agent/
├── yad2/                          # Real estate scraping package
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
│   └── examples/                  # Example scripts & configs
│       ├── __init__.py
│       ├── demo.py                # Demonstration script
│       └── search_config.json     # Example configuration
├── rami/                          # Israeli planning documents (RAMI)
│   ├── __init__.py
│   ├── rami_client.py             # RAMI TabaSearch API client
│   └── mcp/                       # MCP server for planning data
│       ├── __init__.py
│       └── server.py              # FastMCP server implementation
├── gis/                           # GIS utilities (Tel Aviv ArcGIS)
│   ├── __init__.py
│   ├── gis_client.py              # Tel Aviv GIS client and mini CLI
│   ├── parse_zchuyot.py           # Building privilege parser
│   └── mcp/                       # MCP server for GIS data
│       ├── __init__.py
│       └── server.py              # FastMCP server implementation
├── gov/                           # Government data utilities
│   └── mcp/                       # MCP server for gov.il data
│       ├── __init__.py
│       ├── constants.py
│       ├── decisive.py            # Decisive appraisal data
│       └── server.py              # FastMCP server implementation
├── tests/                         # Comprehensive test suite
│   ├── __init__.py
│   ├── test_utils.py              # Robust import utilities
│   ├── conftest.py                # Pytest configuration
│   ├── robust_imports_template.py # Template for new test files
│   ├── yad2/                      # Yad2 tests
│   ├── rami/                      # RAMI tests
│   ├── gis/                       # GIS tests
│   └── gov/                       # Government data tests
├── db/                            # Database models
│   ├── __init__.py
│   ├── database.py
│   └── models.py
├── utils/                         # Utility scripts
│   ├── madlan_scraper.py
│   └── yad2_scraper.py
├── realestate-broker-ui/          # Next.js broker dashboard
├── backend-django/                # Django backend
├── .vscode/                       # VSCode configuration
│   └── launch.json                # Debugger configuration
├── requirements.txt               # Dependencies
├── pyproject.toml                 # Project configuration
├── run_all.sh                     # Start all MCP servers
├── LICENSE                        # License
└── README.md                      # This file
```

## 🚀 Quick Start

### 1. Installation

Ensure you have Python 3.10 or later installed. Creating an isolated
virtual environment is recommended so that dependencies do not conflict
with other projects.

```bash
# Clone the repository
git clone <your-repo-url>
cd realestate-agent

# (Optional) create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

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

### 2. Broker UI (optional)

A web dashboard lives in `realestate-broker-ui/` for brokers to review listings, set up alerts, and run mortgage analysis.

```bash
# frontend
cd realestate-broker-ui
pnpm install
cp .env.example .env.local
pnpm dev

# backend
cd ../backend-django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 3. Usage

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

#### Alerts (optional)

Send email or WhatsApp alerts when a listing matches your criteria.

```python
from alerts import EmailAlert, Notifier

alert = EmailAlert("user@example.com")
notifier = Notifier({"city": 5000}, [alert])
for listing in listings:
    notifier.notify(listing)
```

#### RAMI (Planning Documents) Usage

- Python API:
```python
from rami.rami_client import RamiClient

# Search for Tel Aviv plans
client = RamiClient()
search_params = {
    "city": 5000,  # Tel Aviv
    "planTypes": [72, 21, 1, 8, 9, 10, 12, 20],
    "planTypesUsed": True
}
plans_df = client.fetch_plans(search_params)
print(f"Found {len(plans_df)} plans")

# Download documents for specific plans
plans_list = plans_df.head(3).to_dict('records')
results = client.download_multiple_plans_documents(
    plans_list, 
    doc_types=['takanon', 'tasrit'],  # Regulations and blueprints
    base_dir="planning_docs"
)
```

- Run Examples:
```bash
# Download planning documents example
python tests/rami/download_example.py

# Test MCP server
python tests/rami/test_mcp_server.py
```

#### GIS (Tel Aviv) Usage

- CLI (quick check):
```bash
python -m gis.gis_client --street "הגולן" --num 1 --radius 30
```

- Python API:
```python
from gis.gis_client import TelAvivGS

gs = TelAvivGS()
x, y = gs.get_address_coordinates("הגולן", 1)
permits = gs.get_building_permits(x, y, radius=30, download_pdfs=True, save_dir="permits")
print(len(permits))
```

## 🏛️ RAMI Planning Documents System

### Israeli Planning Document Types

The RAMI system provides access to official Israeli planning documents from land.gov.il:

- **תקנון (takanon)**: Planning regulations and legal requirements (PDF)
- **תשריט (tasrit)**: Blueprints, drawings, and planning maps (PDF)  
- **נספח (nispach)**: Supporting appendices and additional documentation (PDF)
- **ממ"ג (mmg)**: Digital planning archives with CAD files and data (ZIP)

### Search Parameters

- **Plan Number**: Specific plan identifier (e.g., "תמ\"א 38", "מתא/7")
- **City Code**: Municipality identifier (5000 = Tel Aviv, 6200 = Jerusalem)
- **Gush/Chelka**: Block and plot numbers for precise location targeting
- **Plan Types**: Various planning categories (residential, commercial, infrastructure)
- **Status Filters**: Planning approval stages and dates

### File Organization

Downloaded documents are automatically organized:
```
rami_plans/
└── PlanName_PlanID/
    ├── takanon/     # Regulation PDFs
    ├── tasrit/      # Blueprint PDFs  
    ├── nispach/     # Appendix PDFs
    └── mmg/         # ZIP archives
```

## 🔧 Yad2 Search Parameters

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

## 🤖 MCP Servers for LLM Integration

Multiple specialized MCP servers provide comprehensive real estate intelligence through LLM integration.

### 🏠 Yad2 Real Estate Server

**Available Tools:**
1. `search_real_estate` — Search listings with natural language
2. `get_search_parameters_reference` — Get parameter documentation
3. `analyze_search_results` — Analyze price trends, locations, property types
4. `save_search_results` — Save results to JSON file
5. `build_search_url` — Generate Yad2 URLs without scraping

**Start:** `python -m yad2.mcp.server`

### 🏛️ RAMI Planning Documents Server

**Available Tools:**
1. `search_plans` — General search for planning documents
2. `search_tel_aviv_plans` — Pre-configured Tel Aviv area search
3. `download_plan_documents` — Download documents for specific plan
4. `download_multiple_plans_documents` — Bulk document downloads
5. `get_document_types_info` — Information about available document types

**Start:** `python -m rami.mcp.server`

**Document Types:**
- **takanon** (תקנון): Planning regulations (PDF)
- **tasrit** (תשריט): Blueprints and drawings (PDF)
- **nispach** (נספח): Supporting appendices (PDF)
- **mmg** (ממ"ג): Digital planning archives (ZIP)

### 🗺️ Tel Aviv GIS Server

**Available Tools:**
1. `geocode_address` — Convert addresses to coordinates
2. `get_building_permits` — Find nearby construction permits
3. `get_land_use_main` — Get main land use categories
4. `get_land_use_detailed` — Get detailed land use data
5. `get_plans_local` — Get local planning data
6. `get_plans_citywide` — Get city-wide planning data
7. `get_parcels` — Get parcel information
8. `get_blocks` — Get block information
9. `get_dangerous_buildings` — Find dangerous buildings nearby
10. `get_preservation` — Find preserved buildings
11. `get_noise_levels` — Get noise level data
12. `get_cell_antennas` — Find cellular antennas
13. `get_green_areas` — Find parks and green spaces
14. `get_shelters` — Find bomb shelters
15. `get_building_privilege_page` — Download building privilege pages

**Start:** `python -m gis.mcp.server`

### 📊 Government Data Server

**Available Tools:**
1. `status_show` — Get CKAN version and extensions
2. `package_search` — Search government datasets
3. `package_show` — Get specific dataset details
4. `fetch_comparable_transactions` — Get comparable real estate transactions
5. `decisive_appraisal` — Get decisive appraisal decisions

**Start:** `python -m gov.mcp.server`

### 🚀 Usage with LLM

**Start All Servers:**
```bash
./run_all.sh
```

**Individual Servers:**
```bash
python -m yad2.mcp.server     # Real estate scraping
python -m rami.mcp.server     # Planning documents
python -m gis.mcp.server      # Tel Aviv GIS data
python -m gov.mcp.server      # Government datasets
```

**Configure your LLM** to connect to the servers and use natural language queries:

**Real Estate Queries:**
- "Find 4-room apartments in Tel Aviv under 8 million NIS with parking"
- "Search for penthouses in Jerusalem with elevator"
- "Analyze the price distribution of the last search"

**Planning Document Queries:**
- "Find planning documents for Gush 6638 Chelka 96"
- "Download blueprints for plan תמ\"א 38 in Tel Aviv"
- "Search for all approved plans in Tel Aviv from 2023"

**GIS & Location Queries:**
- "Get coordinates for Rothschild 1 Tel Aviv"
- "Find building permits near Dizengoff 50"
- "What's the land use for coordinates 184320, 668548?"

**Government Data Queries:**
- "Find comparable real estate transactions near my address"
- "Get decisive appraisal decisions for block 6638"

## 🧪 Testing

### Comprehensive Test Suite

The project includes extensive testing across all modules with robust import handling.

**Run All Tests:**
```bash
pytest -q
```

**Run Specific Module Tests:**
```bash
# Yad2 real estate tests
python -m yad2.tests.test_core

# RAMI planning document tests
python tests/rami/test_rami_client.py
python tests/rami/test_mcp_server.py

# GIS tests
python tests/gis/test_gis_client.py

# Government data tests
python tests/gov/test_decisive_appraisal.py

# Test robust import system
python tests/rami/test_robust_imports.py
```

**Run Examples:**
```bash
# Download planning documents
python tests/rami/download_example.py

# Test RAMI pagination
python tests/rami/test_pagination.py
```

### Test Coverage

**Yad2 (Real Estate):**
- Parameter system validation
- URL building and parsing  
- Data model functionality
- Scraper behaviors (mocked HTTP)
- MCP server integration

**RAMI (Planning Documents):**
- API client functionality
- Document download system
- PDF/ZIP file handling
- MCP server tools
- Search parameter validation

**GIS (Tel Aviv):**
- Address geocoding
- Spatial data queries
- Building permit searches
- MCP server integration

**Government Data:**
- Dataset searches
- Decisive appraisal data
- Comparable transactions

### Robust Import System

All test files use a robust import system that works in **all environments**:
- ✅ **Terminal execution**: `python tests/module/test_file.py`
- ✅ **VS Code debugger**: F5 debugging with breakpoints  
- ✅ **Pytest**: `pytest tests/`
- ✅ **CI/CD**: Automated testing pipelines

**For New Test Files:**

Copy this template to ensure imports work everywhere:

```python
import sys
import os
from pathlib import Path

def setup_python_path():
    """Robust path setup for all environments."""
    try:
        import tests.test_utils  # Preferred method
        return
    except (ImportError, ModuleNotFoundError):
        pass
    
    # Fallback: find project root
    current_file = Path(__file__).resolve()
    current_dir = current_file.parent
    
    for _ in range(5):  # Max 5 levels up
        has_config = any((current_dir / marker).exists() 
                        for marker in ['pyproject.toml', 'requirements.txt'])
        has_rami = (current_dir / 'rami').exists()
        
        if has_config and has_rami:  # Found project root
            if str(current_dir) not in sys.path:
                sys.path.insert(0, str(current_dir))
            return
        
        current_dir = current_dir.parent

setup_python_path()

# Now imports work reliably:
from rami.rami_client import RamiClient
```

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
2. **Module not found errors in tests**: Use the robust import template provided in the Testing section
3. **Debugger import issues**: Ensure `.vscode/launch.json` has `"cwd": "${workspaceFolder}"`
4. **No listings found**: Check if parameters are too restrictive
5. **Rate limiting**: Increase delay between requests
6. **Parsing errors**: Yad2 may have changed their HTML structure
7. **PDF download failures**: Check network connection and RAMI API status
8. **MCP server connection issues**: Verify server is running and ports are available

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Import Issues

If you encounter import problems in test files:

1. **Use the robust import template** from the Testing section
2. **Verify project structure**: Ensure you're in the project root with `rami/`, `gis/`, `yad2/` directories
3. **Check working directory**: Run `pwd` to confirm you're in `/path/to/realestate-agent`
4. **Test the import system**:
   ```bash
   python tests/rami/test_robust_imports.py
   ```

### MCP Server Issues

If MCP servers won't start:

1. **Check dependencies**: `pip install -r requirements.txt`
2. **Verify Python path**: Ensure project root is accessible
3. **Test individual servers**:
   ```bash
   python -c "from yad2.mcp.server import mcp; print('Yad2 OK')"
   python -c "from rami.mcp.server import mcp; print('RAMI OK')"
   python -c "from gis.mcp.server import mcp; print('GIS OK')"
   ```
4. **Check ports**: Ensure no conflicts on default MCP ports

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

## 🚀 **Ready for Comprehensive Real Estate Intelligence!**

**🏠 Search Real Estate** • **🏛️ Access Planning Documents** • **🗺️ Analyze GIS Data** • **📊 Get Government Insights**

**All through natural language with your LLM! 🤖**

### Key Capabilities Summary

- **🔍 Real Estate Search**: Comprehensive Yad2 scraping with 58+ search parameters
- **📄 Planning Documents**: Download Israeli planning documents (תקנון, תשריט, נספח, ממ"ג)  
- **🗺️ GIS Intelligence**: Tel Aviv spatial data, permits, land use, and more
- **📊 Government Data**: Comparable transactions, decisive appraisals, datasets
- **🤖 LLM Integration**: 4 specialized MCP servers with 25+ tools
- **🧪 Robust Testing**: Works in terminal, debugger, pytest - all environments
- **🔧 Developer Friendly**: Comprehensive documentation, examples, and templates