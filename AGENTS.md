# AGENTS

This monorepo contains several independent projects:

- `backend-django/` – Django backend and API. Related tests live under `tests/core`.
- `yad2/`, `rami/`, `gis/`, `mavat/`, `gov/` – API clients and scrapers for external services. Each has tests under `tests/<name>/`.
- `realestate-broker-ui/` – React/Next.js UI with its own unit tests and end-to-end tests.

## Guidelines

- Run tests for the components you modify:
  - Backend or collectors: `pytest` (e.g. `pytest tests/core` or `pytest tests/yad2`).
  - UI: `npm test` in `realestate-broker-ui` (use `npm run test:e2e` for Playwright tests).
- Use `rg` for searching across the codebase.
- Avoid using `ls -R` or `grep -R` for performance reasons.
