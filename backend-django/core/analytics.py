"""Analytics helper utilities.

DISABLED: Using Vercel Analytics and Google Analytics instead.
This module provides no-op stubs to maintain compatibility with existing code.
"""

from typing import Optional, Dict, Any


def track(
    event: str,
    *,
    user=None,
    asset_id: Optional[int] = None,
    source: Optional[str] = None,
    error_code: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def get_top_failures(days: int = 30, limit: int = 10):
    """No-op - analytics disabled."""
    return []


def track_page_view(
    session_id: str,
    page_path: str,
    *,
    user=None,
    page_title: str = "",
    load_time: float = 0.0,
    duration: float = 0.0,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_session_end(session_id: str, duration: float = 0.0) -> None:
    """No-op - analytics disabled."""
    pass


def track_marketing_message(
    message_type: str,
    *,
    user=None,
    asset_id: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_search(
    query: str,
    *,
    user=None,
    filters: Optional[Dict[str, Any]] = None,
    results_count: int = 0,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_feature_usage(
    feature: str,
    *,
    user=None,
    asset_id: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_performance(
    metric: str,
    value: float,
    *,
    user=None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_calculator_usage(
    calculator_type: str,
    action: str,
    *,
    user=None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_calculator_calculation(
    calculator_type: str,
    input_data: Dict[str, Any],
    result_data: Optional[Dict[str, Any]] = None,
    *,
    user=None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def track_calculator_export(
    calculator_type: str,
    export_format: str,
    *,
    user=None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """No-op - analytics disabled."""
    pass


def rollup_day(date):
    """No-op - analytics disabled."""
    return None
