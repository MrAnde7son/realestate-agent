from rest_framework import viewsets, permissions
from .models import Asset, Permit, Plan
from .serializers import AssetSerializer, PermitSerializer, PlanSerializer

import logging

logger = logging.getLogger(__name__)


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        asset = serializer.save()
        logger.info("Asset created with id %s", asset.id)


class PermitViewSet(viewsets.ModelViewSet):
    queryset = Permit.objects.all()
    serializer_class = PermitSerializer
    permission_classes = [permissions.AllowAny]


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
