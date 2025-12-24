# Archive Directory

This directory contains one-time migration scripts and deprecated utilities that are kept for reference but are no longer actively used.

## Files

### `fix_token_blacklist.py`
One-time database migration script used to fix NULL user_id values in the token_blacklist_outstandingtoken table before a Django migration.

**Status:** Deprecated - No longer needed after migration was completed.

**Original Location:** `backend-django/fix_token_blacklist.py`

**Usage (historical):**
```bash
cd backend-django
python fix_token_blacklist.py
python manage.py migrate
```

---

**Note:** These scripts are kept for historical reference and should not be run unless you understand their purpose and impact.

