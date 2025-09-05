from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SupportTicket, ConsultationRequest
from .serializers import ConsultationRequestSerializer
from .support_notify import notify_ticket, notify_consultation


@api_view(["POST"])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def support_contact(request):
    data = request.data
    t = SupportTicket.objects.create(
        user=request.user,
        kind="contact",
        subject=data.get("subject", ""),
        message=data.get("message", ""),
    )
    notify_ticket(t)
    return Response({"ok": True, "id": t.id}, status=201)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def support_bug(request):
    f = request.FILES.get("attachment")
    t = SupportTicket.objects.create(
        user=request.user,
        kind="bug",
        subject=request.data.get("subject", "דיווח באג"),
        message=request.data.get("message", ""),
        severity=request.data.get("severity", ""),
        url=request.data.get("url", ""),
        user_agent=request.data.get("user_agent", ""),
        app_version=request.data.get("app_version", ""),
    )
    if f:
        t.attachment = f
        t.save(update_fields=["attachment"])
    notify_ticket(t)
    return Response({"ok": True, "id": t.id}, status=201)


@api_view(["POST"])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def support_consultation(request):
    s = ConsultationRequestSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    obj = s.save(user=request.user)
    notify_consultation(obj)
    return Response({"ok": True, "id": obj.id}, status=201)
