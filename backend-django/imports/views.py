from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ImportBatch
from .serializers import ImportBatchSerializer
from .tasks import run_nadlanone_import


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "yes", "on"}


class NadlanOneImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mode = request.data.get("mode")
        if mode not in {ImportBatch.MODE_CUSTOMERS, ImportBatch.MODE_PROPERTIES}:
            return Response({"error": "Invalid mode"}, status=status.HTTP_400_BAD_REQUEST)

        customers_file = request.FILES.get("customers_csv")
        properties_file = request.FILES.get("properties_csv")

        if mode == ImportBatch.MODE_CUSTOMERS and not customers_file:
            return Response({"error": "customers_csv is required"}, status=status.HTTP_400_BAD_REQUEST)
        if mode == ImportBatch.MODE_PROPERTIES and not properties_file:
            return Response({"error": "properties_csv is required"}, status=status.HTTP_400_BAD_REQUEST)

        conflict_policy = request.data.get("conflict_policy", "update")
        if conflict_policy not in {"update", "skip"}:
            return Response({"error": "Invalid conflict_policy"}, status=status.HTTP_400_BAD_REQUEST)

        dry_run = _parse_bool(request.data.get("dry_run"))
        enable_linking = _parse_bool(request.data.get("enable_linking"))

        batch = ImportBatch.objects.create(
            source="nadlan_one",
            mode=mode,
            tenant=request.user,
            user=request.user,
            dry_run=dry_run,
            conflict_policy=conflict_policy,
            enable_linking=enable_linking,
        )

        if customers_file:
            batch.customers_csv.save(customers_file.name or "customers.csv", customers_file, save=True)
        if properties_file:
            batch.properties_csv.save(properties_file.name or "properties.csv", properties_file, save=True)

        run_nadlanone_import.delay(str(batch.id), mode, dry_run, conflict_policy, enable_linking)

        return Response({"batch_id": str(batch.id), "status": batch.status}, status=status.HTTP_201_CREATED)


class ImportBatchDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, batch_id):
        try:
            batch = ImportBatch.objects.get(id=batch_id)
        except ImportBatch.DoesNotExist:
            return None
        if not (batch.tenant_id == user.id or user.is_staff or user.is_superuser):
            return None
        return batch

    def get(self, request, batch_id):
        batch = self.get_object(request.user, batch_id)
        if not batch:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ImportBatchSerializer(batch, context={"request": request})
        return Response(serializer.data)

    def post(self, request, batch_id):
        action = request.data.get("action")
        if action != "cancel":
            return Response({"error": "Unsupported action"}, status=status.HTTP_400_BAD_REQUEST)

        batch = self.get_object(request.user, batch_id)
        if not batch:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        if batch.status not in {ImportBatch.STATUS_PENDING, ImportBatch.STATUS_RUNNING}:
            return Response({"error": "Cannot cancel in current status"}, status=status.HTTP_400_BAD_REQUEST)

        batch.mark_cancelled()
        serializer = ImportBatchSerializer(batch, context={"request": request})
        return Response(serializer.data)


class ImportBatchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ImportBatch.objects.filter(tenant=request.user)
        mode = request.query_params.get("mode")
        if mode in {ImportBatch.MODE_CUSTOMERS, ImportBatch.MODE_PROPERTIES}:
            qs = qs.filter(mode=mode)
        qs = qs.order_by("-created_at")
        serializer = ImportBatchSerializer(qs, many=True, context={"request": request})
        return Response({"results": serializer.data})
