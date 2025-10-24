import uuid
from django.conf import settings
from django.db import models


def _report_upload_path(instance, filename):
    return f"imports/nadlan_one/{instance.id}/{filename}"


def _source_upload_path(instance, filename):
    return f"imports/nadlan_one/{instance.id}/source/{filename}"


class ImportBatch(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_RUNNING = "RUNNING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    MODE_CUSTOMERS = "customers"
    MODE_PROPERTIES = "properties"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=50)
    mode = models.CharField(max_length=50)
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_import_batches",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="import_batches",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    totals = models.JSONField(default=dict)
    dry_run = models.BooleanField(default=False)
    conflict_policy = models.CharField(max_length=20, default="update")
    enable_linking = models.BooleanField(default=False)
    customers_csv = models.FileField(upload_to=_source_upload_path, null=True, blank=True)
    properties_csv = models.FileField(upload_to=_source_upload_path, null=True, blank=True)
    report_csv = models.FileField(upload_to=_report_upload_path, null=True, blank=True)
    report_json = models.FileField(upload_to=_report_upload_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "mode"]),
            models.Index(fields=["status"]),
            models.Index(fields=["user"]),
        ]

    def mark_cancelled(self):
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=["status", "updated_at"])
