"""Analytics helper utilities."""
from datetime import timedelta
from typing import Optional, Dict, Any

from django.db import models
from django.utils import timezone

from .models import AnalyticsEvent, AnalyticsDaily


def track(
    event: str,
    *,
    user=None,
    asset_id: Optional[int] = None,
    source: Optional[str] = None,
    error_code: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Store a raw analytics event.

    Fails silently to avoid interfering with application flow.
    """
    try:
        AnalyticsEvent.objects.create(
            event=event,
            user=user,
            asset_id=asset_id,
            source=source,
            error_code=error_code,
            meta=meta or {},
        )
    except Exception:
        # Do not raise analytics errors
        pass


def get_top_failures(days: int = 30, limit: int = 10):
    start = timezone.now().date() - timedelta(days=days - 1)
    return list(
        AnalyticsEvent.objects.filter(
            event__in=['collector_fail', 'report_fail', 'alert_fail', 'asset_sync_fail'],
            created_at__date__gte=start,
        )
        .values('source', 'error_code')
        .annotate(count=models.Count('id'))
        .order_by('-count')[:limit]
    )


def rollup_day(date):
    events = AnalyticsEvent.objects.filter(created_at__date=date)
    daily, _ = AnalyticsDaily.objects.get_or_create(date=date)
    daily.users = events.filter(event='user_signup').count()
    daily.assets = events.filter(event='asset_create').count()
    daily.reports = events.filter(event='report_success').count()
    daily.alerts = events.filter(event='alert_send').count()
    daily.errors = events.filter(
        event__in=['report_fail', 'alert_fail', 'collector_fail', 'asset_sync_fail']
    ).count()
    daily.save()
    return daily
