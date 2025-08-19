import json
import sys
from pathlib import Path

from django.test import RequestFactory

from db.database import SQLAlchemyDatabase
from db import models


def _setup_db(tmp_path: Path) -> SQLAlchemyDatabase:
    db = SQLAlchemyDatabase(f"sqlite:///{tmp_path}/test.db")
    db.init_db()
    with db.get_session() as session:
        session.add_all([
            models.Listing(
                source="test",
                external_id="1",
                property_type="apartment",
                address="Street 1, Tel Aviv",
            ),
            models.Listing(
                source="test",
                external_id="2",
                property_type="house",
                address="Street 2, Jerusalem",
            ),
            models.Listing(
                source="test",
                external_id="3",
                property_type="apartment",
                address="Street 3, Tel Aviv",
            ),
        ])
        session.commit()
    return db


def _setup_views(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "backend-django"))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
    import django
    django.setup()
    import core.views as views
    db = _setup_db(tmp_path)
    monkeypatch.setattr(views, "SQLAlchemyDatabase", lambda: db)
    return views


def test_property_type_distribution(tmp_path, monkeypatch):
    views = _setup_views(monkeypatch, tmp_path)
    rf = RequestFactory()
    req = rf.get("/api/analytics/property-types")
    res = views.property_type_distribution(req)
    assert res.status_code == 200
    data = json.loads(res.content)
    assert {"property_type": "apartment", "count": 2} in data["rows"]
    assert {"property_type": "house", "count": 1} in data["rows"]


def test_market_activity_by_area(tmp_path, monkeypatch):
    views = _setup_views(monkeypatch, tmp_path)
    rf = RequestFactory()
    req = rf.get("/api/analytics/market-activity")
    res = views.market_activity_by_area(req)
    assert res.status_code == 200
    data = json.loads(res.content)
    assert {"area": "Tel Aviv", "count": 2} in data["rows"]
    assert {"area": "Jerusalem", "count": 1} in data["rows"]
