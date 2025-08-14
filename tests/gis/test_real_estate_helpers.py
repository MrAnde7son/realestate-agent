import pytest
from gis.gis_client import TelAvivGS

def test_haversine_distance():
    assert TelAvivGS._haversine(0, 0, 0, 1) == pytest.approx(111195, rel=1e-3)

def test_norm_field():
    rec = {"A": "", "B": "value"}
    assert TelAvivGS._norm_field(rec, ["A", "B"]) == "value"

def test_try_date():
    assert TelAvivGS._try_date("01/02/2024") == "2024-02-01"

def test_to_float():
    assert TelAvivGS._to_float("1,234.5") == 1234.5

def test_median():
    assert TelAvivGS._median([1, 3, 2]) == 2
    assert TelAvivGS._median([1, 2, 3, 4]) == 2.5

def test_process_transaction_record():
    record = {
        "עיר": "תל אביב-יפו",
        "רחוב": "Test",
        "מספר_בית": "1",
        "תאריך_עסקה": "2023-01-01",
        "שווי_עסקה": "1,000,000",
        "שטח_דירה": "100",
        "lat": 32.0,
        "lon": 34.0,
    }
    comp = TelAvivGS._process_transaction_record(record, 32.0, 34.0, None, None, None)
    assert comp is not None
    assert comp["price_sqm"] == 10000
    assert comp["distance_m"] == 0
    assert (
        TelAvivGS._process_transaction_record(record, 32.0, 34.0, None, None, 50)
        is None
    )
