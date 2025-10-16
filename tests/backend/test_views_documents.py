import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = ROOT / "backend-django"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from core.views_documents import _update_asset_from_tabu


class DummyAsset:
    """Simple stand-in for the Asset model used in tests."""

    def __init__(self):
        self.id = 1
        self.owner_name = None
        self.ownership_percentage = None
        self.meta = None
        self.block = None
        self.parcel = None
        self.subparcel = None
        self.total_area = None
        self.area = None
        self.save_called = False

    def save(self):
        self.save_called = True


def test_update_asset_from_tabu_sets_parcel_details_without_owners():
    asset = DummyAsset()
    tabu_rows = [
        {"field": "גוש", "value": "123"},
        {"field": "חלקה", "value": "45"},
        {"field": "תת חלקה", "value": "3"},
    ]

    _update_asset_from_tabu(asset, tabu_rows)

    assert asset.block == "123"
    assert asset.subparcel == "3"
    assert asset.save_called is True
    assert asset.owner_name is None
    assert asset.ownership_percentage is None
