from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .permissions import IsAdmin
from .models import AnalyticsDaily, AnalyticsEvent


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
