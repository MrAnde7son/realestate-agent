# Nadlaner™

Nadlaner™ is a comprehensive real estate intelligence platform designed for brokers, appraisers, and real estate professionals in Israel. Features advanced MCP (Model Context Protocol) server integration for seamless LLM use, Israeli real estate scraping (Yad2), planning document access (RAMI), Tel Aviv GIS integration, and professional broker tools.

Nadlaner™ is a trademark of MrAnde7son.

## 🎯 Core Features

### 🏠 Real Estate Intelligence & Scraping
- **🔍 Advanced Search**: Comprehensive Yad2 scraping with 58+ search parameters
- **📊 Market Analytics**: Price analysis, location breakdowns, property type distributions
- **💾 Data Export**: Save results to JSON with comprehensive metadata
- **📈 Trend Analysis**: Historical price tracking and market insights
- **🎯 Smart Filtering**: Location, price range, property features, and amenities
- **📄 Property Documents**: Attach land registry extracts, condo plans, and area appraisals manually, while permits and rights documents are collected automatically

### 🖥️ Professional Broker Dashboard
- **📋 Asset Management**: Modern Next.js interface for property portfolio management
- **👥 CRM System**: Complete client and lead management with contact tracking, lead status management, and automated analytics
- **🚨 Real-time Alerts**: Email and WhatsApp notifications with Celery task scheduling
- **💰 Mortgage Calculator**: Advanced affordability analysis and Bank of Israel rate integration
- **📊 Visual Analytics**: Interactive charts and market insights with Recharts
- **🛡️ Role-Based Access**: Admin-only analytics dashboard for monitoring users, assets, reports, alerts, and errors
- **🗺️ Map Integration**: Mapbox GL integration for property visualization
- **📱 Responsive Design**: Mobile-friendly interface with dark/light theme support
- **⏱️ Rate-Limited Asset Creation**: API endpoint enforces rate limits and returns a job ID for asynchronous processing
- **📝 Per-Field Provenance**: Track the source of each property attribute for transparency

### 🏛️ Planning & Government Data (RAMI)
- **📄 Israeli Planning Documents**: Direct access to land.gov.il TabaSearch API
- **🗂️ Document Downloads**: Automatic download of regulations (תקנון), blueprints (תשריט), appendices (נספח), and archives (ממ"ג)
- **🔍 Smart Search**: Search by plan number, city, block/parcel, or multiple criteria
- **🇮🇱 Tel Aviv Optimized**: Pre-configured searches for Tel Aviv metropolitan area

### 🗺️ GIS & Location Intelligence
- **📍 Address Geocoding**: Convert addresses to coordinates (EPSG:2039)
- **🏗️ Building Permits**: Find nearby construction permits with PDF downloads
- **🌍 Spatial Analysis**: Land use, zoning, parcels, and neighborhood data
- **🔒 Safety Data**: Dangerous buildings, preservation status, noise levels
- **📋 Building Rights**: Access building privilege (זכויות בנייה) information

### 🤖 AI & LLM Integration
- **🤖 Multiple MCP Servers**: 4 specialized servers (Yad2, RAMI, GIS, gov.il) with 25+ tools
- **🌐 Natural Language Queries**: Ask questions in plain language
- **⚡ URL Builder**: Generate search URLs programmatically without scraping
- **🔧 Development Tools**: Robust testing and debugging capabilities
- **📚 Comprehensive Documentation**: Parameter references and examples

## 📁 Project Architecture

```
realestate-agent/
├── 🏠 CORE SCRAPING & MCP SERVICES
│   ├── yad2/                      # Real estate scraping & MCP server
│   │   ├── core/                  # Core functionality
│   │   │   ├── parameters.py      # Search parameters & validation (58+ params)
│   │   │   ├── models.py          # Data models (RealEstateAsset)
│   │   │   └── utils.py           # Utility functions
│   │   ├── scrapers/              # Web scrapers
│   │   │   └── yad2_scraper.py    # Main Yad2 scraper with rate limiting
│   │   ├── mcp/server.py          # MCP server for LLM integration
│   │   ├── cli/interactive.py     # Interactive CLI utilities
│   │   └── examples/demo.py       # Demonstration script
│   ├── gis/                       # Tel Aviv GIS integration
│   │   ├── gis_client.py          # Tel Aviv ArcGIS client & CLI
│   │   ├── parse_zchuyot.py       # Building privilege parser
│   │   └── mcp/server.py          # GIS data MCP server
│   ├── mavat/                     # National planning portal (MAVAT) tools
│   └── gov/                       # Government data services (includes transactions, RAMI and decisive)
│       └── mcp/                   # Gov.il data MCP server
│           ├── server.py          # Government datasets & comparables
│           ├── decisive.py        # Decisive appraisal data
│           └── transactions.py    # Real estate transaction data
├── 🖥️ PROFESSIONAL UI & BACKEND
│   ├── realestate-broker-ui/      # Next.js 15 Professional Dashboard
│   │   ├── app/                   # App Router (Next.js 15)
│   │   │   ├── assets/          # Property assets management
│   │   │   ├── crm/              # CRM system (contacts & leads)
│   │   │   ├── alerts/            # Alert configuration
│   │   │   ├── mortgage/          # Mortgage calculator & analysis
│   │   │   └── api/               # API routes
│   │   ├── components/            # Reusable UI components
│   │   │   ├── layout/            # Layout components (sidebar, header)
│   │   │   ├── ui/                # Shadcn/ui components
│   │   │   ├── crm/               # CRM-specific components
│   │   │   ├── AssetsTable.tsx   # Advanced assets table
│   │   │   └── Map.tsx            # Mapbox GL map integration
│   │   ├── lib/                   # Utilities & configuration
│   │   │   ├── data.ts            # Data interfaces & types
│   │   │   ├── api/               # API client modules
│   │   │   │   └── crm.ts         # CRM API client
│   │   │   ├── mortgage.ts        # Mortgage calculation logic
│   │   │   └── config.ts          # App configuration
│   │   └── types/                 # TypeScript definitions
│   └── backend-django/            # Django Backend API
│       ├── broker_backend/        # Django project configuration
│       │   ├── settings.py        # Django settings with Celery
│       │   ├── celery.py          # Celery configuration
│       │   └── urls.py            # URL routing
│       ├── core/                  # Core Django app
│       │   ├── models.py          # Database models
│       │   ├── views.py           # API views
│       │   ├── tasks.py           # Celery tasks for alerts
│       │   └── urls.py            # API endpoints
│       └── crm/                   # CRM Django app
│           ├── models.py          # Contact & Lead models
│           ├── views.py           # CRM API views
│           ├── serializers.py     # CRM data serializers
│           ├── analytics.py       # Event tracking & analytics
│           └── permissions.py     # CRM access control
├── 🧪 TESTING & UTILITIES
│   ├── tests/                     # Comprehensive test suite
│   │   ├── yad2/                  # Real estate scraping tests
│   │   ├── gov/                   # Government data tests
│   │   ├── gis/                   # GIS integration tests
│   │   └── core/                  # Integration tests
│   ├── db/                        # Database utilities
│   ├── utils/                     # Utility scripts
│   └── orchestration/             # Alert scheduling & management
├── 📋 CONFIGURATION & DEPLOYMENT
│   ├── claude_config.json         # Claude Desktop MCP configuration
│   ├── requirements.txt           # Python dependencies
│   ├── pyproject.toml            # Project configuration
│   └── run_all.sh                # Start all MCP servers
```

## 🚀 Quick Start

### 📋 Prerequisites
- **Python 3.10+** (recommended: 3.11 or 3.12)
- **Node.js 18+** (for the broker UI)
- **pnpm** (for package management)
- **Redis** (for Django backend alerts, optional)

### 1️⃣ Core Installation

```bash
# Clone the repository
git clone https://github.com/your-username/realestate-agent.git
cd realestate-agent

# Create and activate virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2️⃣ Professional Broker Dashboard (Recommended)

The modern Next.js dashboard provides a complete broker workflow with alerts, mortgage analysis, and property management.

```bash
# 🖥️ Frontend Setup
cd realestate-broker-ui
pnpm install
# Create .env.local file with your configuration (see env.example in project root)
# Example .env.local content:
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
# NEXT_PUBLIC_MCP_YAD2_URL=http://localhost:8001
# NEXT_PUBLIC_MCP_RAMI_URL=http://localhost:8002
# NEXT_PUBLIC_MCP_GIS_URL=http://localhost:8003
# NEXT_PUBLIC_MCP_GOV_URL=http://localhost:8004
# NEXT_PUBLIC_MCP_MAVAT_URL=http://localhost:8005
pnpm dev

# 🔧 Backend Setup (in a new terminal)
cd ../backend-django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python setup_auth.py  # Runs migrations and creates demo/admin users
# Default credentials:
#   admin@example.com / admin123
#   demo@example.com  / demo123
python manage.py runserver 0.0.0.0:8000
```

### 🛠️ Local Development Workflow

Use the project-level helper scripts to get a full stack running quickly. The new [Local Development Guide](docs/LOCAL_DEVELOPMENT.md) walks through each step in detail.

1. **Bootstrap Django automatically** with `./dev_start.sh`. The script copies `env.development`, runs migrations via `setup_auth.py`, seeds demo assets, and finally launches the API on `http://localhost:8000`.
2. **Run the Next.js dashboard** from `realestate-broker-ui/` with `pnpm dev` and the `.env.local` template shown above.
3. **Start MCP servers** either individually (`python -m yad2.mcp_server`, etc.) or all at once with `./run_all.sh` so LLM clients and the dashboard can reach data sources.
4. **Optional Celery/Redis stack** – when testing alerts, start `redis-server` plus `celery -A broker_backend worker` and `celery -A broker_backend beat` in separate terminals. These commands are summarised in the backend README as well.

The combination provides end-to-end parity with production flows, allowing you to test scraping, alerts, and UI interactions locally.

#### 🚨 Enable Real-time Alerts (Optional)
For email/WhatsApp notifications, set up Redis and Celery:

```bash
# Terminal 1: Redis server
redis-server

# Terminal 2: Celery worker
cd backend-django
celery -A broker_backend worker -l info

# Terminal 3: Celery beat scheduler
celery -A broker_backend beat -l info
```

Add environment variables to `backend-django/.env`:
```env
RESEND_API_KEY=your_resend_key
RESEND_FROM="RealEstate Agent <no-reply@yourcompany.com>"
RESEND_REPLY_TO=support@yourcompany.com
RESEND_SANDBOX=true
EMAIL_FALLBACK_TO_CONSOLE=true
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
RESEND_WEBHOOK_SECRET=your_resend_webhook_secret
```

**Frontend Environment Variables:**
Create `realestate-broker-ui/.env.local`:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_MCP_YAD2_URL=http://localhost:8001
NEXT_PUBLIC_MCP_RAMI_URL=http://localhost:8002
NEXT_PUBLIC_MCP_GIS_URL=http://localhost:8003
NEXT_PUBLIC_MCP_GOV_URL=http://localhost:8004
NEXT_PUBLIC_MCP_MAVAT_URL=http://localhost:8005
```

### 2️⃣ CRM System Features

The platform includes a comprehensive CRM system for managing clients and leads:

#### Contact Management
- **Client Database**: Store contact information, phone numbers, emails, and tags
- **Contact Search**: Advanced search and filtering capabilities
- **Contact Analytics**: Track contact creation, updates, and interactions
- **Bulk Operations**: Import/export contacts, bulk updates

#### Lead Management
- **Lead Tracking**: Track leads from initial contact to closing
- **Status Management**: Lead status workflow (New → Contacted → Qualified → Proposal → Negotiation → Closed Won/Lost)
- **Lead Notes**: Add timestamped notes and activity tracking
- **Asset Association**: Link leads to specific properties
- **Lead Analytics**: Conversion tracking and performance metrics

#### CRM Dashboard
- **Overview Statistics**: Total contacts, active leads, conversion rates
- **Recent Activity**: Latest contacts and lead updates
- **Performance Metrics**: Lead conversion analysis and trends
- **Quick Actions**: Fast access to common CRM operations

#### CRM API Endpoints
- `GET /api/crm/contacts` - List contacts with pagination and search
- `POST /api/crm/contacts` - Create new contact
- `GET /api/crm/leads` - List leads with filtering
- `POST /api/crm/leads` - Create new lead
- `PATCH /api/crm/leads/{id}/status` - Update lead status
- `POST /api/crm/leads/{id}/notes` - Add lead note

### 4️⃣ MCP Servers for LLM Integration

Set up Claude Desktop or other LLM tools to use natural language queries:

```bash
# Copy MCP configuration
# macOS:
mkdir -p "${HOME}/Library/Application Support/Claude"
cp claude_config.json "${HOME}/Library/Application Support/Claude/claude_desktop_config.json"

# Linux:
mkdir -p "${HOME}/.config/Claude"
cp claude_config.json "${HOME}/.config/Claude/claude_desktop_config.json"

# Windows (PowerShell):
New-Item -ItemType Directory -Force "$env:APPDATA\Claude" | Out-Null
Copy-Item -Force .\claude_config.json "$env:APPDATA\Claude\claude_desktop_config.json"
```

**Start All MCP Servers:**
```bash
./run_all.sh
```

**Individual Servers:**
```bash
python -m yad2.mcp_server      # Real estate scraping (port 8001)
python -m gis.mcp_server       # Tel Aviv GIS (port 8002)
python -m gov.mcp_server       # Government data (port 8003)
python -m mavat.mcp_server     # National planning portal (port 8004)
```

## 📚 Documentation Index

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) – system diagrams, service breakdowns, and component responsibilities.
- [LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md) – step-by-step developer setup for backend, frontend, MCP, and Celery stacks.
- [INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) – production GCP topology and Terraform deployment instructions.
- [WORKFLOWS.md](docs/WORKFLOWS.md) – broker onboarding cookbook and day-to-day operational playbooks.
- [MCP_TOOLS.md](docs/MCP_TOOLS.md) – reference documentation for available Model Context Protocol tools.

### 5️⃣ Quick Examples

#### 🔍 Search Real Estate (CLI)
```bash
# Interactive CLI
python -c "from yad2.cli import InteractiveCLI; InteractiveCLI().main_menu()"
```

#### 🤖 Natural Language Queries (with Claude/LLM)
After setting up MCP servers, you can ask:
- *"Find 4-room apartments in Tel Aviv under 8 million NIS with parking"*
- *"Get planning documents for Block 6638 Percel 96"*
- *"Find building permits near Dizengoff 50"*
- *"Analyze comparable transactions in Ramat Aviv"*

#### 💻 Programmatic Usage
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

# Search and save results
scraper = Yad2Scraper(params)
assets = scraper.scrape_all_pages(max_pages=3)
scraper.save_to_json("tel_aviv_search.json")

print(f"Found {len(assets)} assets")
```

### 6️⃣ Testing

```bash
# Run all tests
pytest

# Run specific module tests
python -m yad2.tests.test_core
python tests/gov/test_rami_client.py
python tests/gis/test_gis_client.py
python tests/gov/test_decisive_appraisal.py
python tests/crm/test_crm_models.py
python tests/crm/test_crm_views.py
```

#### RAMI (Planning Documents) Usage

- Python API:
```python
from gov.rami.rami_client import RamiClient

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
python tests/gov/download_example.py

# Test MCP server
python tests/gov/test_mcp_server.py
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
- **Block/Percel**: Block and plot numbers for precise location targeting
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
- `shelter`: Has safe room (1=yes, 0=no)

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
assets = scraper.scrape_all_pages(max_pages=2)
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

The platform provides **5 specialized MCP servers** with **25+ tools** for comprehensive real estate intelligence through natural language queries.

### 🏠 Yad2 Real Estate Server (`python -m yad2.mcp_server`)

**API Client Tools:**
- **`fetch_listings`** — Fetch active listings via Yad2's public map feed API (supports all 58+ search parameters)
- **`fetch_contact_info`** — Fetch contact information for a listing token
- **`fetch_project_autocomplete`** — Fetch project data from Yad1 developers autocomplete API
- **`fetch_location_autocomplete`** — Fetch location data from Yad2 address autocomplete API and return prepared search parameters
- **`fetch_latest_deals`** — Fetch completed deal records from Yad2's latest-deals endpoint

**Utility Tools:**
- **`get_search_parameters_reference`** — Complete parameter documentation reference
- **`get_all_property_types`** — Get all property type codes with Hebrew and English names

**Example Queries:**
- *"Find 4-room apartments in Tel Aviv under 8M NIS with parking and elevator"*
- *"Search penthouses in Jerusalem with balcony, renovated, price range 5-15M"*
- *"Get contact information for listing token abc123"*
- *"Search for location 'רמת החייל תל אביב'"*
- *"Fetch latest deals in Tel Aviv"*

### 🗺️ Tel Aviv GIS Server (`python -m gis.mcp_server`)

**Spatial Analysis Tools:**
- **`geocode_address`** — Address to coordinates (EPSG:2039)
- **`get_building_permits`** — Nearby construction permits + PDF downloads
- **`get_land_use_main/detailed`** — Land use and zoning data
- **`get_plans_local/citywide`** — Planning data at different scales
- **`get_parcels/blocks`** — Property boundaries and block info
- **`get_dangerous_buildings`** — Safety hazard locations
- **`get_noise_levels`** — Environmental noise data
- **`get_cell_antennas`** — Cellular infrastructure
- **`get_green_areas`** — Parks and green spaces
- **`get_shelters`** — Bomb shelter locations
- **`get_building_privilege_page`** — Building rights (זכויות בנייה)

**Example Queries:**
- *"Get coordinates for Rothschild 1 Tel Aviv"*
- *"Find building permits within 50m of Dizengoff 50"*
- *"What's the land use classification for coordinates 184320, 668548?"*

### 🏛️ Government Data Server (`python -m gov.mcp_server`)

**Data Access Tools:**
- **`package_search/show`** — Search government datasets (data.gov.il)
- **`fetch_comparable_transactions`** — Real estate transaction comparables
- **`decisive_appraisal`** — Decisive appraisal decisions
- **`datastore_search`** — Query structured government data
- **`license_list`** — Available data licenses
- **`organization_list/show`** — Government organizations and their data

**RAMI Planning Document Tools:**
- **`search_plans`** — General planning document search
- **`download_plan_documents`** — Download specific plan documents
- **`download_multiple_plans_documents`** — Bulk downloads
- **`get_document_types_info`** — Available document types reference

**Document Types:**
- **תקנון (takanon)** — Planning regulations (PDF)
- **תשריט (tasrit)** — Blueprints and drawings (PDF)  
- **נספח (nispach)** — Supporting appendices (PDF)
- **ממ"ג (mmg)** — Digital planning archives (ZIP)

**Example Queries:**
- *"Find comparable real estate transactions near my address"*
- *"Get decisive appraisal decisions for block 6638 plot 96"*
- *"Search government datasets about housing prices"*
- *"Find planning documents for Block 6638 Percel 96"*
- *"Download blueprints for plan תמ״א 38 in Tel Aviv"*

### 🏛️ MAVAT Planning Portal Server (`python -m mavat.mcp_server`)

**Planning Tools:**
- **`search_plans`** — Search for planning documents by various criteria
- **`get_plan_details`** — Get detailed information for specific plans
- **`get_plan_documents`** — Download plan documents and attachments
- **`search_by_location`** — Location-based plan searches
- **`search_by_block_parcel`** — Cadastral-based searches
- **`get_lookup_tables`** — Access reference data (districts, cities, streets)
- **`get_plan_summary`** — Comprehensive plan summaries

**Example Queries:**
- *"Find planning documents for Tel Aviv city center"*
- *"Search plans by block 6638 parcel 96"*
- *"Get all approved plans in Jerusalem from 2023"*

### 🚀 Usage with LLM

**Start All Servers:**
```bash
./run_all.sh
```

**Individual Servers:**
```bash
python -m yad2.mcp_server     # Real estate scraping
python -m gis.mcp_server       # Tel Aviv GIS data
python -m gov.mcp_server       # Government datasets
python -m mavat.mcp_server     # National planning portal
```

**Configure your LLM** to connect to the servers and use natural language queries:

**Real Estate Queries:**
- "Find 4-room apartments in Tel Aviv under 8 million NIS with parking"
- "Search for penthouses in Jerusalem with elevator"
- "Get contact information for a specific listing"
- "Search for location 'רמת החייל תל אביב'"
- "Fetch latest completed deals in Tel Aviv"

**Planning Document Queries:**
- "Find planning documents for Block 6638 Parcel 96"
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
python tests/gov/test_rami_client.py
python tests/gov/test_mcp_server.py

# GIS tests
python tests/gis/test_gis_client.py

# Government data tests
python tests/gov/test_decisive_appraisal.py

# Test robust import system
python tests/gov/test_robust_imports.py
```

**Run Examples:**
```bash
# Download planning documents
python tests/gov/download_example.py

# Test RAMI pagination
python tests/gov/test_pagination.py
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
from gov.rami.rami_client import RamiClient
```

## 📊 Data Export Format

Results are saved in JSON format with:
- Search metadata (parameters, URL, timestamp)
- Individual asset details (price, address, features, images)
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
  "total_assets": 10,
  "assets": [
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

- Start MCP server: `python -m yad2.mcp_server `
- Run tests: `python -m yad2.tests.test_core`
- Interactive CLI: `python -c "from yad2.cli import InteractiveCLI; InteractiveCLI().main_menu()"`

## 🚨 Troubleshooting

### Common Issues

1. **Import errors**: Ensure you ran `pip install -r requirements.txt` and `cd realestate-agent`
2. **Module not found errors in tests**: Use the robust import template provided in the Testing section
3. **Debugger import issues**: Ensure `.vscode/launch.json` has `"cwd": "${workspaceFolder}"`
4. **No assets found**: Check if parameters are too restrictive
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
   python tests/gov/test_robust_imports.py
   ```

### MCP Server Issues

If MCP servers won't start:

1. **Check dependencies**: `pip install -r requirements.txt`
2. **Verify Python path**: Ensure project root is accessible
3. **Test individual servers**:
   ```bash
   python -c "from yad2.mcp_server  import mcp; print('Yad2 OK')"
   python -c "from gov.mcp_server  import mcp; print('GOV OK')"
   python -c "from gis.mcp_server  import mcp; print('GIS OK')"
   ```
4. **Check ports**: Ensure no conflicts on default MCP ports

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite: `python -m yad2.tests.test_core`
5. Submit a pull request

## 📄 License

GNU General Public License v3.0 or later (GPLv3) - see LICENSE file for details.

Nadlaner™ is a trademark of MrAnde7son.

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
