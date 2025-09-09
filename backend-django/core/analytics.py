"""Analytics helper utilities."""
from datetime import timedelta
from typing import Optional, Dict, Any
import uuid

from django.db import models
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .models import AnalyticsEvent, AnalyticsDaily, UserSession, PageView


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
    """Track a page view with session management."""
    try:
        # Get or create session
        session, created = UserSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'ip_address': meta.get('ip_address') if meta else None,
                'user_agent': meta.get('user_agent', '') if meta else '',
                'referrer': meta.get('referrer', '') if meta else '',
            }
        )
        
        # Update session if user is now authenticated
        if user and not session.user:
            session.user = user
            session.save()
        
        # Create page view
        PageView.objects.create(
            session=session,
            user=user,
            page_path=page_path,
            page_title=page_title,
            load_time=load_time,
            duration=duration,
            meta=meta or {},
        )
        
        # Update session page count
        session.page_view_count = PageView.objects.filter(session=session).count()
        session.save()
        
    except Exception:
        # Do not raise analytics errors
        pass


def track_session_end(session_id: str, duration: float = 0.0) -> None:
    """Mark a session as ended."""
    try:
        session = UserSession.objects.get(session_id=session_id)
        session.ended_at = timezone.now()
        session.duration = duration
        session.is_bounce = session.page_view_count <= 1
        session.save()
    except UserSession.DoesNotExist:
        pass
    except Exception:
        # Do not raise analytics errors
        pass


def track_marketing_message(
    message_type: str,
    *,
    user=None,
    asset_id: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Track marketing message creation."""
    track(
        "marketing_message_create",
        user=user,
        asset_id=asset_id,
        meta={
            **(meta or {}),
            "message_type": message_type,
        }
    )


def track_search(
    query: str,
    *,
    user=None,
    filters: Optional[Dict[str, Any]] = None,
    results_count: int = 0,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Track search queries."""
    track(
        "search_performed",
        user=user,
        meta={
            **(meta or {}),
            "query": query,
            "filters": filters or {},
            "results_count": results_count,
        }
    )


def track_feature_usage(
    feature: str,
    *,
    user=None,
    asset_id: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Track feature usage."""
    track(
        "feature_usage",
        user=user,
        asset_id=asset_id,
        meta={
            **(meta or {}),
            "feature": feature,
        }
    )


def track_performance(
    metric: str,
    value: float,
    *,
    user=None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Track performance metrics."""
    track(
        "performance_metric",
        user=user,
        meta={
            **(meta or {}),
            "metric": metric,
            "value": value,
        }
    )


def rollup_day(date):
    """Enhanced rollup function with comprehensive metrics."""
    events = AnalyticsEvent.objects.filter(created_at__date=date)
    sessions = UserSession.objects.filter(started_at__date=date)
    page_views = PageView.objects.filter(viewed_at__date=date)
    
    daily, _ = AnalyticsDaily.objects.get_or_create(date=date)
    
    # Core metrics
    daily.users = events.filter(event='user_signup').count()
    daily.assets = events.filter(event='asset_create').count()
    daily.reports = events.filter(event='report_success').count()
    daily.alerts = events.filter(event='alert_rule_create').count()
    daily.errors = events.filter(
        event__in=['report_fail', 'alert_fail', 'collector_fail', 'asset_sync_fail']
    ).count()
    
    # User engagement metrics
    daily.page_views = page_views.count()
    daily.unique_visitors = sessions.values('user').distinct().count()
    
    # Calculate average session duration
    session_durations = sessions.filter(ended_at__isnull=False).values_list('duration', flat=True)
    daily.session_duration_avg = sum(session_durations) / len(session_durations) if session_durations else 0.0
    
    # Calculate bounce rate
    total_sessions = sessions.count()
    bounce_sessions = sessions.filter(is_bounce=True).count()
    daily.bounce_rate = (bounce_sessions / total_sessions * 100) if total_sessions > 0 else 0.0
    
    # Feature usage metrics
    daily.marketing_messages_created = events.filter(event='marketing_message_create').count()
    daily.searches_performed = events.filter(event='search_performed').count()
    daily.filters_applied = events.filter(event='feature_usage', meta__feature='filter').count()
    daily.exports_downloaded = events.filter(event='feature_usage', meta__feature='export').count()
    
    # Conversion metrics
    daily.signup_conversions = events.filter(event='user_signup').count()
    daily.asset_creation_conversions = events.filter(event='asset_create').count()
    daily.report_generation_conversions = events.filter(event='report_success').count()
    daily.alert_setup_conversions = events.filter(event='alert_rule_create').count()
    
    # Performance metrics
    performance_events = events.filter(event='performance_metric')
    if performance_events.exists():
        page_load_times = performance_events.filter(meta__metric='page_load_time').values_list('meta__value', flat=True)
        daily.avg_page_load_time = sum(page_load_times) / len(page_load_times) if page_load_times else 0.0
        
        api_response_times = performance_events.filter(meta__metric='api_response_time').values_list('meta__value', flat=True)
        daily.api_response_time_avg = sum(api_response_times) / len(api_response_times) if api_response_times else 0.0
    
    # Calculate error rate
    total_events = events.count()
    error_events = events.filter(
        event__in=['report_fail', 'alert_fail', 'collector_fail', 'asset_sync_fail']
    ).count()
    daily.error_rate = (error_events / total_events * 100) if total_events > 0 else 0.0
    
    daily.save()
    return daily
