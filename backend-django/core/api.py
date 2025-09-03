from rest_framework import viewsets, permissions
from .models import Asset, Permit, Plan
from .serializers import AssetSerializer, PermitSerializer, PlanSerializer


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [permissions.AllowAny]


class PermitViewSet(viewsets.ModelViewSet):
    queryset = Permit.objects.all()
    serializer_class = PermitSerializer
    permission_classes = [permissions.AllowAny]


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
