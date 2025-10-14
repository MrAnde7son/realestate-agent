# Handasa search client

The Handasa SharePoint search surface is exposed through `HandasaSearchClient`
in `handasa.client`.  The helper is composed into the existing
`HandasaClient`, giving callers a dynamic payload builder without having to
reimplement the Handasa scraping workflow.  The search layer supports both the
SharePoint REST (`/_api/search/postquery`) and CSOM (`ProcessQuery`) backends
while providing a consistent API for filters, pagination, and select-property
management.

## Usage

```python
from handasa.client import (
    HandasaClient,
    HandasaSearchClient,
    HandasaSearchConfig,
    HandasaSearchFilters,
)

cfg = HandasaSearchConfig(base_url="https://handasa.tel-aviv.gov.il", use_rest=True)
search_client = HandasaSearchClient(cfg)

filters = HandasaSearchFilters(
    blocks_parcels="12345",
    document_type_not_in=[
        "תיק פקוח",
        "פיקוח-אחר",
        "מכתבים/תכתובות-שימור",
        "תביעות,צווים מינהליים",
        "דואר נכנס ויוצא פיקוח על הבניה",
    ],
    publishable=True,
    sort=[("TlvMPEngDocDate", "desc")],
)

result = search_client.search(
    filters=filters,
    row_limit=200,
    all_pages=True,
    select_all_properties=True,
    refiners=[
        "TlvMPEngFolderId(deephits=100000,sort=name/ascending)",
        "TlvMPEngDocumentType(deephits=100000)",
    ],
)

print(result["total_rows"], len(result["items"]))

# Existing HandasaClient now uses the same search helper for get_archive and
# custom queries.
client = HandasaClient()
archive = client.get_archive(block="12345")
custom = client.search_documents(filters, select_all_properties=True)
```

### Filters

`HandasaSearchFilters` provides strongly typed attributes for the available
KQL clauses.  Any list filters (such as `document_type_in`) are converted to the
appropriate KQL `OR` clause while exclusions are handled automatically based on
Handasa defaults.  Date filters accept `YYYY-MM-DD` strings and are expanded to
full-day ranges in UTC.

### Pagination

The `search` method automatically follows additional pages when
`all_pages=True`.  The `row_limit` is clamped to SharePoint's 500 row maximum
and defaults to 100.  When `all_pages=False` only the first page is retrieved,
allowing manual pagination if needed.

### Select properties

The REST backend can opt into returning all retrievable properties by passing
`select_all_properties=True`, which injects `SelectProperties=["*"]` while
retaining the curated base set.  The CSOM backend does not support `*`, so the
client falls back to a curated allowlist of common fields and always includes
any explicit `select_properties` provided.

### Resilience

Timeouts, retries (with exponential backoff and jitter) and a default
200–400 ms delay between REST page requests are built in.  An external `requests`
session can be supplied to reuse authentication cookies when running in the
context of a browser-assisted scraping workflow.
