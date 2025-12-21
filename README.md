# Nadlaner™

Nadlaner™ is a comprehensive real estate intelligence platform designed for brokers, appraisers, and real estate professionals in Israel. Features advanced MCP (Model Context Protocol) server integration for seamless LLM use, Israeli real estate scraping (Yad2), planning document access (RAMI), Tel Aviv GIS integration, and professional broker tools.

Nadlaner™ is a trademark of MrAnde7son.

## 🚀 Quick Reference for Collaborators

**Getting Started:**
- **Installation**: See [Quick Start](#-quick-start) section
- **Development Setup**: Use `./dev_start.sh` for automated setup
- **MCP Servers**: Run `./run_all.sh` to start all MCP servers
- **Testing**: Run `pytest` from project root

**Key Directories:**
- `orchestration/` - Data collection pipeline and collectors
- `backend-django/` - Django REST API
- `realestate-broker-ui/` - Next.js frontend
- `yad2/`, `gis/`, `gov/`, etc. - Data source modules with MCP servers

**Documentation:**
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md) - Developer setup guide
- [WORKFLOWS.md](docs/WORKFLOWS.md) - Operational workflows

**Common Commands:**
```bash
# Start development environment
./dev_start.sh

# Start all MCP servers
./run_all.sh

# Run tests
pytest

# Start Django backend
cd backend-django && python manage.py runserver
# Redis server
redis-server

# Celery worker
celery -A broker_backend worker -l info

# Start Next.js frontend
cd realestate-broker-ui && pnpm dev
```

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
- **📍 Multi-City Support**: Tel Aviv, Bat Yam, Herzliya, Ramat Gan GIS integration
- **📍 Address Geocoding**: Convert addresses to coordinates (EPSG:2039)
- **🏗️ Building Permits**: Find nearby construction permits with PDF downloads
- **🌍 Spatial Analysis**: Land use, zoning, parcels, and neighborhood data
- **🔒 Safety Data**: Dangerous buildings, preservation status, noise levels
- **📋 Building Rights**: Access building privilege (זכויות בנייה) information
- **🚇 Metro Stations**: Red, Green, Purple line proximity data
- **🌳 Green Areas**: Parks and green spaces analysis
- **🚗 Parking**: Public and private parking lot data

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
│   │   ├── mcp_server.py          # MCP server for LLM integration
│   │   ├── cli/interactive.py     # Interactive CLI utilities
│   │   └── api_client.py          # Yad2 API client
│   ├── gis/                       # Multi-city GIS integration
│   │   ├── gis_client.py          # Tel Aviv ArcGIS client & CLI
│   │   ├── proxy_gis_client.py    # Multi-city GIS proxy
│   │   ├── batyam_gis_client.py   # Bat Yam GIS client
│   │   ├── herzliya_gis_client.py # Herzliya GIS client
│   │   ├── ramat_gan_gis_client.py # Ramat Gan GIS client
│   │   ├── parse_zchuyot.py       # Building privilege parser
│   │   └── mcp_server.py          # GIS data MCP server
│   ├── gov/                       # Government data services
│   │   ├── mcp_server.py          # Government data MCP server
│   │   ├── rami/                  # RAMI planning documents
│   │   │   └── rami_client.py     # RAMI API client
│   │   ├── nadlan/                # Real estate transactions
│   │   ├── decisive.py            # Decisive appraisal data
│   │   └── michrazim/             # Tender data
│   ├── govmap/                    # GovMap address & location services
│   │   ├── api_client.py          # GovMap API client
│   │   ├── scraper.py             # GovMap web scraper
│   │   └── mcp_server.py          # GovMap MCP server
│   ├── mavat/                     # National planning portal (MAVAT)
│   │   ├── mavat_api_client.py    # MAVAT API client
│   │   ├── scrapers/              # MAVAT scrapers
│   │   ├── cli.py                 # CLI interface
│   │   └── mcp_server.py          # MAVAT MCP server
│   ├── madlan/                    # Madlan real estate listings
│   │   ├── api_client.py          # Madlan API client
│   │   ├── parser.py              # Data parser
│   │   └── mcp_server.py          # Madlan MCP server
│   └── handasa/                   # Handasa engineering portal
│       ├── client.py              # Handasa API client
│       └── mcp_server.py          # Handasa MCP server
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
│   │   │   ├── AssetsTable.tsx    # Advanced assets table
│   │   │   └── MapView.tsx        # MapLibre GL map integration
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
│       │   ├── pdf_generator.py   # PDF report generation
│       │   └── services/          # Business logic services
│       ├── crm/                   # CRM Django app
│       │   ├── models.py          # Contact & Lead models
│       │   ├── views.py           # CRM API views
│       │   ├── serializers.py     # CRM data serializers
│       │   ├── analytics.py       # Event tracking & analytics
│       │   └── permissions.py     # CRM access control
│       └── api_mcp/               # API MCP server
│           ├── server.py           # FastMCP server for API integration
│           └── views.py           # Django HTTP endpoint
├── 🔄 DATA ORCHESTRATION & PIPELINE
│   ├── orchestration/             # Data collection orchestration
│   │   ├── data_pipeline.py       # Main data pipeline orchestrator
│   │   ├── collectors/            # Data collectors
│   │   │   ├── base_collector.py  # Base collector interface
│   │   │   ├── yad2_collector.py # Yad2 data collector
│   │   │   ├── madlan_collector.py # Madlan data collector
│   │   │   ├── gis_collector.py   # GIS data collector
│   │   │   ├── municipal_gis.py    # Multi-city GIS adapter
│   │   │   ├── gov_collector.py    # Government data collector
│   │   │   ├── govmap_collector.py # GovMap data collector
│   │   │   ├── mavat_collector.py  # MAVAT data collector
│   │   │   ├── rami_collector.py   # RAMI data collector
│   │   │   ├── handasa_collector.py # Handasa data collector
│   │   │   └── michrazim_collector.py # Tender data collector
│   │   ├── pipeline/              # Data processing pipeline
│   │   │   ├── asset_enrichment.py # Asset data enrichment
│   │   │   ├── asset_expansion.py  # Related asset expansion
│   │   │   ├── listings.py         # Listing normalization
│   │   │   └── documents.py        # Document processing
│   │   ├── alerts.py              # Alert notification system
│   │   ├── scheduler.py           # Task scheduling
│   │   ├── observability.py       # Prometheus metrics & OpenTelemetry
│   │   └── location.py            # Location query handling
│   └── db/                        # Database layer
│       ├── database.py            # SQLAlchemy database setup
│       └── models.py              # Database models
├── 🧪 TESTING & UTILITIES
│   ├── tests/                     # Comprehensive test suite
│   │   ├── yad2/                  # Real estate scraping tests
│   │   ├── gov/                   # Government data tests
│   │   ├── gis/                   # GIS integration tests
│   │   ├── mavat/                 # MAVAT tests
│   │   ├── orchestration/          # Pipeline tests
│   │   └── e2e/                   # End-to-end tests
│   ├── utils/                     # Utility scripts
│   └── scripts/                   # Development scripts
├── 📋 CONFIGURATION & DEPLOYMENT
│   ├── claude_config.json         # Claude Desktop MCP configuration
│   ├── requirements.txt            # Python dependencies (aggregates all)
│   ├── pyproject.toml              # Project configuration
│   ├── run_all.sh                  # Start all MCP servers
│   ├── dev_start.sh                # Development startup script
│   ├── docker-compose.yml           # Docker Compose configuration
│   └── infra/                      # Infrastructure as code
│       └── gcp/                    # GCP Terraform configurations
```

## 🚀 Quick Start

### 📋 Prerequisites
- **Python 3.10+** (recommended: 3.11 or 3.12)
- **Node.js 18+** (for the broker UI, recommended: 20 LTS)
- **pnpm** (for package management)
- **Redis** (for Django backend alerts and Celery, optional)
- **PostgreSQL** (recommended for production) or SQLite (development)

### 1️⃣ Core Installation

```bash
# Clone the repository
git clone https://github.com/your-username/realestate-agent.git
cd realestate-agent

# Create and activate virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
# This installs all module dependencies (backend, orchestration, GIS, etc.)
pip install -r requirements.txt

# Or install module-specific requirements:
pip install -r backend-django/requirements.txt
pip install -r orchestration/requirements.txt
pip install -r gis/requirements.txt
pip install -r gov/requirements.txt
# ... etc
```

### 2️⃣ Professional Broker Dashboard (Recommended)

The modern Next.js dashboard provides a complete broker workflow with alerts, mortgage analysis, and property management.

```bash
# 🖥️ Frontend Setup
cd realestate-broker-ui
pnpm install
pnpm dev

# 🔧 Backend Setup (in a new terminal)
cd ../backend-django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python setup_auth.py  # Runs migrations and creates demo/admin users
python manage.py runserver 0.0.0.0:8000
```

### 🛠️ Local Development Workflow

Use the project-level helper scripts to get a full stack running quickly. The new [Local Development Guide](docs/LOCAL_DEVELOPMENT.md) walks through each step in detail.

1. **Bootstrap Django automatically** with `./dev_start.sh`. The script copies `env.development`, runs migrations via `setup_auth.py`, seeds demo assets, and finally launches the API on `http://localhost:8000`.
2. **Run the Next.js dashboard** from `realestate-broker-ui/` with `pnpm dev` and the `.env.local` template shown above.
3. **Start MCP servers** either individually (`python -m yad2.mcp_server`, etc.) or all at once with `./run_all.sh` so LLM clients and the dashboard can reach data sources.
4. **Optional Celery/Redis stack** – when testing alerts, start `redis-server` plus `celery -A broker_backend worker` and `celery -A broker_backend beat` in separate terminals. These commands are summarised in the backend README as well.

The combination provides end-to-end parity with production flows, allowing you to test scraping, alerts, and UI interactions locally.

#### 🚨 Enable Celery Broker & Alerts (Optional)

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

### 4️⃣ Data Pipeline & Orchestration

The orchestration layer provides a unified data collection framework that aggregates data from multiple sources:

```python
from orchestration.data_pipeline import DataPipeline
from orchestration.location import LocationQuery

# Create pipeline instance
pipeline = DataPipeline()

# Collect data for a location
location = LocationQuery(street="רוזוב", house_number=18, city="תל אביב")
result = pipeline.collect_all(location)

# Access collected data
yad2_listings = result.get('yad2', [])
gis_data = result.get('gis', {})
gov_data = result.get('gov', {})
```

**Available Collectors:**
- **Yad2Collector**: Real estate listings from Yad2
- **MadlanCollector**: Madlan property listings
- **MultiCityGISCollector**: GIS data from Tel Aviv, Bat Yam, Herzliya, Ramat Gan
- **GovCollector**: Government datasets and transactions
- **GovMapCollector**: GovMap location and deal data
- **MavatCollector**: MAVAT planning documents
- **RamiCollector**: RAMI planning documents
- **HandasaCollector**: Handasa engineering projects
- **MichrazimCollector**: Tender data

**Observability:**
- **Prometheus Metrics**: Collector latency, success/failure counters
- **OpenTelemetry Tracing**: Distributed tracing for data collection
- **Metrics Endpoint**: Available at `http://localhost:9000/metrics` (configurable via `METRICS_PORT`)

**Configuration:**
```bash
# Set metrics port
export METRICS_PORT=9000

# Enable tracing (optional)
export ENABLE_TRACING=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

### 5️⃣ MCP Servers for LLM Integration

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
python -m yad2.mcp_server      # Real estate scraping
python -m gis.mcp_server        # Multi-city GIS data
python -m gov.mcp_server        # Government datasets & RAMI
python -m mavat.mcp_server      # National planning portal
python -m madlan.mcp_server     # Madlan listings
python -m govmap.mcp_server     # GovMap location services
python -m handasa.mcp_server    # Handasa engineering portal
# API MCP server runs as part of Django backend at /mcp/
```

## 📚 Documentation Index

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) – system diagrams, service breakdowns, and component responsibilities.
- [LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md) – step-by-step developer setup for backend, frontend, MCP, and Celery stacks.
- [INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) – production GCP topology and Terraform deployment instructions.
- [WORKFLOWS.md](docs/WORKFLOWS.md) – broker onboarding cookbook and day-to-day operational playbooks.
- [MCP_TOOLS.md](docs/MCP_TOOLS.md) – reference documentation for available Model Context Protocol tools.

### 6️⃣ Quick Examples

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

### 7️⃣ Testing

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

The platform provides **8 specialized MCP servers** with **50+ tools** for comprehensive real estate intelligence through natural language queries.

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

### 🗺️ Multi-City GIS Server (`python -m gis.mcp_server`)

**Spatial Analysis Tools:**
- **`geocode_address`** — Address to coordinates (EPSG:2039) - supports Tel Aviv, Bat Yam, Herzliya, Ramat Gan
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
- **`get_metro_stations`** — Metro stations (Red, Green, Purple lines)
- **`get_parking_lots`** — Public and private parking lots
- **`get_affordable_housing_projects`** — Affordable housing pipeline
- **`get_bike_paths`** — Bicycle path accessibility

**Supported Cities:**
- Tel Aviv (primary)
- Bat Yam
- Herzliya
- Ramat Gan

**Example Queries:**
- *"Get coordinates for Rothschild 1 Tel Aviv"*
- *"Find building permits within 50m of Dizengoff 50"*
- *"What's the land use classification for coordinates 184320, 668548?"*
- *"Find metro stations within 1km of this address"*

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
- **`search_by_block_parcel`** — Cadastral-based searches
- **`get_lookup_tables`** — Access reference data (districts, cities, streets)
- **`get_plan_summary`** — Comprehensive plan summaries

**Example Queries:**
- *"Find planning documents for Tel Aviv city center"*
- *"Search plans by block 6638 parcel 96"*
- *"Get all approved plans in Jerusalem from 2023"*

### 🏘️ Madlan Real Estate Server (`python -m madlan.mcp_server`)

**Listing Tools:**
- **`get_addresses`** — Autocomplete addresses and get address details
- **`madlan_search_real_estate`** — Search for real estate listings with filters

**Example Queries:**
- *"Search for apartments in Tel Aviv with 3-4 rooms under 5M NIS"*
- *"Find rental properties in Ramat Gan"*

### 🗺️ GovMap Location Server (`python -m govmap.mcp_server`)

**Location Tools:**
- **`autocomplete`** — Address autocomplete from GovMap
- **`extract_coordinates_from_shapes`** — Extract ITM coordinates from results
- **`coordinate_conversion`** — Convert between ITM and WGS84
- **`get_parcel_data`** — Get parcel data for coordinates
- **`get_deals_by_location`** — Get real estate deals for location and radius

**Example Queries:**
- *"Get coordinates for Rothschild 1 Tel Aviv"*
- *"Find deals within 100m of this address"*

### 🏗️ Handasa Engineering Portal Server (`python -m handasa.mcp_server`)

**Engineering Tools:**
- **`search_projects`** — Search engineering projects
- **`get_project_details`** — Get detailed project information

**Example Queries:**
- *"Find engineering projects in Tel Aviv"*

### 🔌 API MCP Server (`backend-django/api_mcp/server.py`)

**API Integration Tools:**
- **Assets**: Property assets and enriched data
- **Deal Expenses**: Deals, negotiations, and offers with financial information
- **Expense Calculation**: Building construction cost estimation
- **Mortgage Calculation**: Mortgage affordability analysis
- **CRM**: Contacts, leads, tasks, meetings, and interactions
- **File Reading**: Read-only file reading for permits, zchuyot, tabu documents

**Usage:**
- Runs as part of Django backend at `/mcp/` endpoint
- Can be used standalone: `python backend-django/api_mcp/server.py`
- See `backend-django/api_mcp/README.md` for details

### 🚀 Usage with LLM

**Start All Servers:**
```bash
./run_all.sh
```

**Individual Servers:**
```bash
python -m yad2.mcp_server      # Real estate scraping
python -m gis.mcp_server        # Multi-city GIS data
python -m gov.mcp_server        # Government datasets & RAMI
python -m mavat.mcp_server       # National planning portal
python -m madlan.mcp_server      # Madlan listings
python -m govmap.mcp_server      # GovMap location services
python -m handasa.mcp_server     # Handasa engineering portal
# API MCP server runs as part of Django backend at /mcp/
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
# Run all tests with pytest
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration # Run only integration tests
```

**Run Specific Module Tests:**
```bash
# Yad2 real estate tests
python -m yad2.tests.test_core
pytest tests/yad2/

# RAMI planning document tests
python tests/gov/test_rami_client.py
pytest tests/gov/

# GIS tests
python tests/gis/test_gis_client.py
pytest tests/gis/

# Government data tests
python tests/gov/test_decisive_appraisal.py

# Orchestration and pipeline tests
pytest tests/orchestration/

# MAVAT tests
pytest tests/mavat/

# End-to-end tests
pytest tests/e2e/

# Django backend tests
cd backend-django
python manage.py test
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

**Core Services:**
- **yad2/**: Real estate scraping and API client
- **gis/**: Multi-city GIS integration (Tel Aviv, Bat Yam, Herzliya, Ramat Gan)
- **gov/**: Government data services (RAMI, Nadlan, Decisive)
- **mavat/**: National planning portal integration
- **madlan/**: Madlan real estate listings
- **govmap/**: GovMap location services
- **handasa/**: Handasa engineering portal

**Orchestration:**
- **orchestration/**: Data collection pipeline and orchestration
  - **collectors/**: Data collectors for each source
  - **pipeline/**: Data processing and enrichment
  - **observability.py**: Prometheus metrics and OpenTelemetry tracing

**Backend & Frontend:**
- **backend-django/**: Django REST API with Celery
- **realestate-broker-ui/**: Next.js 15 dashboard

### Development Workflow

**1. Local Development Setup:**
```bash
# Use the development startup script
./dev_start.sh

# Or manually:
cd backend-django
python setup_auth.py  # Initialize database and create users
python manage.py runserver
```

**2. Adding New Collectors:**
```python
# Create a new collector in orchestration/collectors/
from orchestration.collectors.base_collector import BaseCollector

class MyCollector(BaseCollector):
    def collect(self, location=None, **kwargs):
        # Implement collection logic
        return collected_data
```

**3. Adding MCP Tools:**
```python
# Add tools to the appropriate mcp_server.py
from mcp import Context

@mcp.tool()
async def my_new_tool(ctx: Context, param: str):
    """Tool description for LLM."""
    return result
```

**4. Testing:**
```bash
# Run tests for specific module
pytest tests/module_name/

# Run with coverage
pytest --cov=module_name --cov-report=html
```

### Entry Points

**MCP Servers:**
- `python -m yad2.mcp_server` - Real estate scraping
- `python -m gis.mcp_server` - GIS data
- `python -m gov.mcp_server` - Government data
- `python -m mavat.mcp_server` - Planning portal
- `python -m madlan.mcp_server` - Madlan listings
- `python -m govmap.mcp_server` - GovMap services
- `python -m handasa.mcp_server` - Handasa portal

**Data Pipeline:**
- `python -c "from orchestration.data_pipeline import DataPipeline; pipeline = DataPipeline(); pipeline.collect_all(...)"`

**CLI Tools:**
- `python -c "from yad2.cli import InteractiveCLI; InteractiveCLI().main_menu()"`
- `python -m gis.gis_client --street "הגולן" --num 1`

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

We welcome contributions! Here's how to get started:

### Getting Started

1. **Fork the repository** and clone your fork
2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up development environment**:
   ```bash
   ./dev_start.sh  # Sets up Django backend
   cd realestate-broker-ui && pnpm install  # Sets up frontend
   ```

### Development Guidelines

**Code Style:**
- Follow PEP 8 for Python code
- Use type hints where possible
- Follow OOP principles (SOLID)
- Keep code simple and maintainable
- Avoid duplicated code

**Testing:**
- Add tests for all new functionality
- Run tests before submitting: `pytest`
- Ensure test coverage doesn't decrease
- Use appropriate test markers (`@pytest.mark.slow`, `@pytest.mark.integration`)

**Documentation:**
- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update API documentation if adding endpoints
- Keep examples up to date

**Pull Request Process:**
1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes and commit with clear messages
3. Run tests: `pytest`
4. Update documentation as needed
5. Push to your fork and create a pull request
6. Ensure CI checks pass

### Module-Specific Guidelines

**Adding a New Collector:**
- Inherit from `BaseCollector` in `orchestration/collectors/base_collector.py`
- Implement the `collect()` method
- Add tests in `tests/orchestration/`
- Register in `orchestration/collectors/__init__.py`

**Adding a New MCP Server:**
- Create `mcp_server.py` in the module directory
- Use FastMCP for tool definitions
- Add tool descriptions for LLM context
- Test with MCP client tools

**Adding Backend Features:**
- Follow Django best practices
- Add migrations for model changes
- Update API documentation
- Add tests in `backend-django/tests/`

**Adding Frontend Features:**
- Use TypeScript for type safety
- Follow component patterns in `components/`
- Add tests in `__tests__/`
- Ensure responsive design

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

- **🔍 Real Estate Search**: Comprehensive Yad2 and Madlan scraping with 58+ search parameters
- **📄 Planning Documents**: Download Israeli planning documents (תקנון, תשריט, נספח, ממ"ג) from RAMI and MAVAT
- **🗺️ Multi-City GIS Intelligence**: Tel Aviv, Bat Yam, Herzliya, Ramat Gan spatial data, permits, land use, and more
- **📊 Government Data**: Comparable transactions, decisive appraisals, datasets, and tender information
- **🔄 Data Pipeline**: Unified orchestration layer for collecting and enriching property data
- **📊 Observability**: Prometheus metrics and OpenTelemetry tracing for monitoring
- **🤖 LLM Integration**: 8 specialized MCP servers with 50+ tools for natural language queries
- **🖥️ Professional Dashboard**: Next.js 15 UI with CRM, alerts, mortgage analysis, and mapping
- **🧪 Robust Testing**: Comprehensive test suite with pytest, works in all environments
- **🔧 Developer Friendly**: Comprehensive documentation, examples, and templates
