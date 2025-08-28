import types

from yad2 import scheduler


def test_load_user_notifiers_initializes_for_each_active_alert(monkeypatch):
    calls = []

    def fake_create(user, criteria):
        calls.append((user, criteria))
        return object()

    monkeypatch.setattr(scheduler, "create_notifier_for_user", fake_create)

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

    monkeypatch.setattr(scheduler, "Alert", DummyAlertModel)

    notifiers = scheduler._load_user_notifiers()
    assert len(calls) == 2
    assert len(notifiers) == 2
    assert calls[0] == (user1, {"city": "TLV"})
    assert calls[1] == (user2, {"price": 100})

