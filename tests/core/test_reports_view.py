import json
from pathlib import Path
import sys

from django.test import RequestFactory

from db.database import SQLAlchemyDatabase
from db import models


def _setup_db(tmp_path: Path) -> SQLAlchemyDatabase:
    db = SQLAlchemyDatabase(f"sqlite:///{tmp_path}/test.db")
    db.init_db()
    with db.get_session() as session:
        listing = models.Listing(
            source="test",
            external_id="1",
            title="Listing",
            price=1000000,
            address="Tel Aviv",
        )
        session.add(listing)
        session.commit()
        listing_id = listing.id
    return db, listing_id


def test_reports_endpoint_creates_pdf(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "backend-django"))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
    import django
    django.setup()
    import core.views as views

    db, listing_id = _setup_db(tmp_path)
    monkeypatch.setattr(views, "SQLAlchemyDatabase", lambda: db)

    rf = RequestFactory()
    req = rf.post(
        "/api/reports",
        data=json.dumps({"listingId": listing_id}),
        content_type="application/json",
    )
    res = views.reports(req)
    assert res.status_code == 201
    data = json.loads(res.content)
    filename = data["report"]["filename"]
    assert (tmp_path / filename).exists()

    req_get = rf.get("/api/reports")
    res_get = views.reports(req_get)
    data_get = json.loads(res_get.content)
    assert len(data_get["reports"]) == 1
