# Real Estate Broker UI (with Alerts + Mortgage Analyzer)

- Listings table with appraisal/rights/env/finance insights
- Listing detail with tabs
- Alerts form at `/alerts` (posts to Django backend `NEXT_PUBLIC_API_BASE_URL`)
- Mortgage analyzer at `/mortgage/analyze`

## Run
```bash
# frontend
cd realestate-broker-ui
pnpm i   
cp .env.example .env.local
pnpm dev

# backend
cd ../backend-django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
