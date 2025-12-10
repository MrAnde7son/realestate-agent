# Israel Building Rights and Permits Scaling Strategy

## Goals
- Deliver nationwide coverage for permits and building rights while maintaining deep, high-fidelity insights where demand is highest.
- Standardize core entities so downstream valuation and recommendation layers stay stable regardless of source.

## Approach
### Hybrid coverage tiers
- **Tier 1 (Deep support):** 5–10 core cities with rich, city-specific parsers, business rules, and normalization (e.g., Tel Aviv, Ramat Gan/Givatayim, Ramat Hasharon/Herzliya, Rishon Lezion, Haifa, Jerusalem).
- **Tier 2 (Broad support):** Lightweight ingestion via GovMap and national planning systems for all other cities; enrich incrementally with municipal GIS as demand grows.

### Source strategy
- **Central sources:** GovMap, national planning (TABA/מבא"ת/מינהל התכנון), and any exposed APIs from national committees.
- **Municipal GIS:** City-specific layers for easements, floor counts, building ratios, conservation, height limits, and renewal programs. Reuse regional patterns where schemas align.

### Normalized data model
Create a stable schema with room for city-specific extensions.

**Parcel/building rights (core fields):**
- `settlement_id`, `settlement_name`
- `gush`, `helka`, `sub_parcel`
- `zoning_type`
- `max_floors_existing`, `max_floors_allowed`
- `building_ratio_existing`, `building_ratio_allowed`
- `max_units_allowed`, `existing_units`
- `setbacks_front`, `setbacks_side`, `setbacks_back`
- `special_restrictions` (e.g., conservation, Tama 38, height/noise limits, public use)
- `planning_plan_ids`
- `last_update_source`

**Permit (core fields):**
- `permit_id`, `permit_type`, `status`
- `submission_date`, `issue_date`
- `linked_plan_id`, `linked_parcel`
- `area_added_m2`, `floors_added`, `units_added`
- `documents_urls`

### Delivery plan
- **Phase 1:** Implement Tier 1 city-specific extractors/normalizers, aligned to the core schema; focus on reusing parsers between metro clusters.
- **Phase 2:** Expand Tier 2 coverage with GovMap-only ingestion for remaining cities; prioritize upgrades to Tier 1 based on demand.
- **Quality:** Add validation rules per city (e.g., exploitation % bounds, floor limits) and data freshness tracking per source.

### Technical notes
- Encapsulate city adapters using OOP: a base `MunicipalGisAdapter` with per-city subclasses for fetching layers, mapping fields, and applying business rules.
- Keep transformation pipelines pure and testable; add fixtures per city to guard against schema drift.
- Store provenance (source + timestamp) alongside every normalized record to support auditability and UI transparency.
