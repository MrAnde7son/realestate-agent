from celery import shared_task
from django.core.files.base import ContentFile

from .models import ImportBatch
from .worker import process_csvs


@shared_task(bind=True)
def run_nadlanone_import(self, batch_id, mode, dry_run, conflict_policy, enable_linking):
    batch = ImportBatch.objects.get(id=batch_id)
    if batch.status == ImportBatch.STATUS_CANCELLED:
        return
    batch.status = ImportBatch.STATUS_RUNNING
    batch.save(update_fields=["status", "updated_at"])
    try:
        results = process_csvs(batch, mode, dry_run, conflict_policy, enable_linking)
        batch.status = ImportBatch.STATUS_COMPLETED
        batch.totals = results["summary"]
        if results.get("csv_report"):
            batch.report_csv.save(f"{batch_id}.csv", ContentFile(results["csv_report"]))
        if results.get("json_report"):
            batch.report_json.save(f"{batch_id}.json", ContentFile(results["json_report"]))
    except Exception as exc:  # pragma: no cover - defensive
        batch.status = ImportBatch.STATUS_FAILED
        batch.totals = {"error": str(exc)}
        raise
    finally:
        batch.save(update_fields=["status", "totals", "updated_at"])
