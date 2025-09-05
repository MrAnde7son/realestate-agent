import pytest
from django.test import Client

from core.models import Report


@pytest.mark.django_db
def test_report_file_endpoint_serves_pdf(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    filename = "dummy.pdf"
    file_path = reports_dir / filename
    file_path.write_bytes(b"%PDF-1.4 test")

    report = Report.objects.create(
        filename=filename,
        file_path=str(file_path),
        report_type="asset",
        status="completed",
    )

    client = Client()
    resp = client.get(f"/api/reports/file/{filename}")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    body = b"".join(resp.streaming_content)
    assert body.startswith(b"%PDF")
    assert report.file_url == f"/api/reports/file/{filename}"

