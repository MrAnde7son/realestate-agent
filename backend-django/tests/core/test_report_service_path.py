from pathlib import Path

from core.report_service import ReportService


def test_default_reports_dir_backend(monkeypatch):
    base_dir = Path(__file__).resolve().parents[2] / "backend-django"
    monkeypatch.delenv("REPORTS_DIR", raising=False)
    service = ReportService(base_dir)
    expected = base_dir / "reports"
    assert Path(service.reports_dir) == expected.resolve()


def test_reports_dir_env_override(monkeypatch, tmp_path):
    custom = tmp_path / "custom"
    monkeypatch.setenv("REPORTS_DIR", str(custom))
    base_dir = Path(__file__).resolve().parents[2] / "backend-django"
    service = ReportService(base_dir)
    assert Path(service.reports_dir) == custom.resolve()

