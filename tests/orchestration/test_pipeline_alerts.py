import types

from orchestration import data_pipeline
from orchestration.data_pipeline import DataPipeline
from db.database import SQLAlchemyDatabase


def test_load_user_notifiers_initializes_for_each_active_alert(monkeypatch):
    calls = []

    def fake_create(user, criteria):
        calls.append((user, criteria))
        return object()

    monkeypatch.setattr(data_pipeline, "create_notifier_for_user", fake_create)

    class DummyUser:
        pass

    user1, user2 = DummyUser(), DummyUser()

    alerts = [
        types.SimpleNamespace(user=user1, criteria={"city": "TLV"}),
        types.SimpleNamespace(user=user2, criteria={"price": 100}),
    ]

    class DummyManager:
        def filter(self, **kwargs):
            assert kwargs == {"active": True}
            return self

        def select_related(self, rel):
            assert rel == "user"
            return alerts

    class DummyAlertModel:
        objects = DummyManager()

    monkeypatch.setattr(data_pipeline, "Alert", DummyAlertModel)

    notifiers = data_pipeline._load_user_notifiers()
    assert len(calls) == 2
    assert len(notifiers) == 2
    assert calls[0] == (user1, {"city": "TLV"})
    assert calls[1] == (user2, {"price": 100})


def test_pipeline_sends_alerts(monkeypatch):
    class DummyYad2:
        def collect(self, address, max_pages):
            return [types.SimpleNamespace(
                title="t", price=1, address="Fake 1", rooms=1,
                floor=1, size=10, property_type="apt", description="",
                url="http://example", listing_id="123", coordinates=(0, 0)
            )]

    class DummyGIS:
        def collect(self, address, house_number):
            return {
                "blocks": [{"ms_gush": "1"}],
                "parcels": [{"ms_chelka": "2"}],
                "block": "1",
                "parcel": "2",
            }

    class DummyGov:
        def collect(self, block, parcel, address):
            return {"decisive": [], "transactions": []}

    class DummyRami:
        def collect(self, block, parcel):
            return []

    class DummyMavat:
        def collect(self, block, parcel, city=None):
            return []

    db = SQLAlchemyDatabase("sqlite:///:memory:")
    pipeline = DataPipeline(db=db, yad2=DummyYad2(), gis=DummyGIS(), gov=DummyGov(), rami=DummyRami(), mavat=DummyMavat())

    class DummyNotifier:
        def __init__(self):
            self.calls = []

        def notify(self, listing):
            self.calls.append(listing.title)

    notifier = DummyNotifier()
    monkeypatch.setattr(data_pipeline, "_load_user_notifiers", lambda: [notifier])

    pipeline.run("Fake", 1)

    assert notifier.calls == ["t"]
