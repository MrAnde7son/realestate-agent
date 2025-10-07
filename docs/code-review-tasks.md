# Code Review Findings (Jan 2025)

## 1. Fix Typo in Marketing Site Pricing Table
- **Issue**: The Hebrew label for the business plan is misspelled as "עיסקי" instead of the correct "עסקי".
- **Location**: `nadlaner-marketing/index.html`, lines 436-448.
- **Proposed Task**: Update the heading and call-to-action text to use the correct spelling to avoid presenting a typo on the public marketing page.

## 2. Correct Property Type Code Mapping Bug
- **Issue**: `PropertyTypeUtils.search_hebrew_name_to_code` returns incorrect Yad2 codes for several property types (e.g., `'דירת גן'` maps to `34` instead of `3`, `'גג'` maps to `35` instead of `6`).
- **Location**: `yad2/utils/property_types.py`, lines 123-155.
- **Proposed Task**: Align the fallback search mapping with the authoritative mapping used elsewhere in the module so that partial-name lookups return the same codes as the canonical translation tables.

## 3. Fix Alert System Documentation Discrepancy
- **Issue**: The alert system guide instructs running `python test_alerts.py`, but no such script exists. Only the Django management command is available.
- **Location**: `docs/alert-system.md`, lines 95-99.
- **Proposed Task**: Update the documentation to reference the supported management command (and/or add the missing script) so readers do not follow a broken instruction.

## 4. Strengthen Mavat Collector Integration Tests
- **Issue**: Two integration tests only contain `assert True`, providing no real coverage.
- **Location**: `tests/mavat/test_collector_integration.py`, lines 13-52.
- **Proposed Task**: Replace the placeholder assertions with real import checks (e.g., actually importing the classes) so the tests fail when modules are missing.
