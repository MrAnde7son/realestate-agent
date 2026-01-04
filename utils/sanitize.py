import re
from typing import Any

_CTRL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def sanitize_for_json(obj: Any) -> Any:
    if obj is None:
        return None

    if isinstance(obj, str):
        return _CTRL.sub("", obj)

    if isinstance(obj, (bytes, bytearray)):
        return _CTRL.sub("", obj.decode("utf-8", errors="replace"))

    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            safe_key = sanitize_for_json(key)
            if not isinstance(safe_key, str):
                safe_key = str(safe_key)
                safe_key = _CTRL.sub("", safe_key)
            out[safe_key] = sanitize_for_json(value)
        return out

    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(item) for item in obj]

    return obj
