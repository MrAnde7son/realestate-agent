# Local Development Guide

This guide explains how to spin up the Nadlaner™ stack on a laptop for iterative development. It complements the high-level architecture overview and focuses on practical day-to-day workflows for backend, frontend, and MCP teams.

## 1. Prerequisites

Before starting, make sure the following tooling is installed locally:

- **Python 3.10+** with `pip` for Django, orchestration utilities, and MCP servers
- **Node.js 18+** with **pnpm** for the Next.js dashboard
- **Redis 6+** (optional but required for Celery-powered alerts)
- **Docker** (optional) if you prefer containerized Postgres/Redis instances

Clone the repository and create a virtual environment in the project root:

```bash
git clone https://github.com/your-username/realestate-agent.git
cd realestate-agent
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

> The root `requirements.txt` installs shared tooling for MCP servers and orchestration helpers. Individual services (Django, Next.js) keep their own lock files.

## 2. Bootstrap the Django Backend

The `dev_start.sh` helper script provisions a development database, seeds demo data, and launches the API server:

```bash
./dev_start.sh
```

The script performs the following steps automatically:

1. Copies `env.development` to `backend-django/.env` if it does not exist yet
2. Executes `backend-django/setup_auth.py` to run migrations and create demo/admin accounts
3. Seeds sample assets through `python manage.py create_sample_assets`
4. Runs `python manage.py runserver` on `http://localhost:8000`

You can stop the server at any time with `Ctrl+C`. When iterating on models or migrations, run the script once for bootstrapping and then use standard Django commands manually.

## 3. Launch the Broker Dashboard (Next.js)

Open a new terminal window to run the React application:

```bash
cd realestate-broker-ui
pnpm install
cp ../env.example .env.local  # adjust hostnames/ports as needed
pnpm dev
```

By default the UI assumes the Django API is available at `http://localhost:8000`. Update `.env.local` if you expose the backend on a different address.

## 4. Start MCP Servers

Model Context Protocol (MCP) servers expose real estate and planning tooling to LLMs and internal scripts. To run every server locally use the bundled helper:

```bash
./run_all.sh
```

Each server binds to a well-known port:

| Service | Module | Default Port |
|---------|--------|--------------|
| Yad2 listings | `python -m yad2.mcp_server` | 8001 |
| RAMI / Government | `python -m gov.mcp_server` | 8003 |
| GIS (Tel Aviv) | `python -m gis.mcp_server` | 8002 |
| National planning (Mavat) | `python -m mavat.mcp_server` | 8004 |

You can also start them individually in separate shells when debugging. Update the Next.js `.env.local` to point to custom hostnames if necessary.

## 5. Optional: Real-time Alerts Stack

Celery and Redis power asynchronous alert delivery. Spin them up when working on alert rules, background tasks, or notifications.

```bash
# Terminal 1
redis-server

# Terminal 2
cd backend-django
celery -A broker_backend worker -l info

# Terminal 3
celery -A broker_backend beat -l info
```

Configure broker/result URLs through `backend-django/.env`. For containerized workflows you can substitute `redis-server` with `docker compose up redis` using the existing `docker-compose.yml`.

## 6. Smoke Testing

After launching the stack:

1. Visit `http://localhost:3000` and log in with the seeded `admin@example.com / admin123` credentials
2. Create an alert and confirm that Celery logs display processing activity (if Redis is running)
3. Verify the Django API is reachable at `http://localhost:8000/api/health/` (returns JSON health payload)

Following these steps ensures the entire developer toolchain is ready for feature work, QA, and integration with LLM-powered flows.
