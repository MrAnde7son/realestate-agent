# put this near other helpers in the file (top-level, once)
def _safe_get(d: dict | None, key: str, default=None):
    """dict.get but tolerates None dict and non-dict child values."""
    if not isinstance(d, dict):
        return default
    v = d.get(key, default)
    return v

def _first_nonempty(*vals):
    for v in vals:
        if v:
            return v
    return None
