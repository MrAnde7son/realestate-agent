from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import json

from .permissions import IsAdmin
from .models import AnalyticsDaily, AnalyticsEvent
from .analytics import track, track_page_view, track_session_end


@api_view(["GET"])
@permission_classes([IsAdmin])
def analytics_timeseries(request):
    today = timezone.now().date()
    start = today - timedelta(days=29)
    daily = AnalyticsDaily.objects.filter(date__gte=start).order_by("date")
    series = [
        {
            "date": d.date.isoformat(),
            "users": d.users,
            "assets": d.assets,
            "reports": d.reports,
            "alerts": d.alerts,
            "errors": d.errors,
            "page_views": d.page_views,
            "unique_visitors": d.unique_visitors,
            "session_duration_avg": d.session_duration_avg,
            "bounce_rate": d.bounce_rate,
            "marketing_messages_created": d.marketing_messages_created,
            "searches_performed": d.searches_performed,
            "filters_applied": d.filters_applied,
            "exports_downloaded": d.exports_downloaded,
            "signup_conversions": d.signup_conversions,
            "asset_creation_conversions": d.asset_creation_conversions,
            "report_generation_conversions": d.report_generation_conversions,
            "alert_setup_conversions": d.alert_setup_conversions,
            "avg_page_load_time": d.avg_page_load_time,
            "api_response_time_avg": d.api_response_time_avg,
            "error_rate": d.error_rate,
        }
        for d in daily
    ]
    return Response({"series": series})


@api_view(["GET"])
@permission_classes([IsAdmin])
def analytics_top_failures(request):
    today = timezone.now().date()
    start = today - timedelta(days=29)
    rows = list(
        AnalyticsEvent.objects.filter(
            event__in=["collector_fail", "report_fail", "alert_fail", "asset_sync_fail"],
            created_at__date__gte=start,
        )
        .values("source", "error_code")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    return Response({"rows": rows})


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def analytics_track(request):
    """Track analytics events from frontend."""
    try:
        data = json.loads(request.body)
        
        track(
            event=data.get("event"),
            user=request.user if request.user.is_authenticated else None,
            asset_id=data.get("asset_id"),
            source=data.get("source"),
            error_code=data.get("error_code"),
            meta=data.get("meta", {}),
        )
        
        return Response({"status": "success"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def analytics_page_view(request):
    """Track page views from frontend."""
    try:
        data = json.loads(request.body)
        
        track_page_view(
            session_id=data.get("session_id"),
            page_path=data.get("page_path"),
            user=request.user if request.user.is_authenticated else None,
            page_title=data.get("page_title", ""),
            load_time=data.get("load_time", 0.0),
            duration=data.get("duration", 0.0),
            meta=data.get("meta", {}),
        )
        
        return Response({"status": "success"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def analytics_session_end(request):
    """Track session end from frontend."""
    try:
        data = json.loads(request.body)
        
        track_session_end(
            session_id=data.get("session_id"),
            duration=data.get("duration", 0.0),
        )
        
        return Response({"status": "success"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)
