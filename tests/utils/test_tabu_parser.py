from utils.parse_tabu import TabuParser


def test_parse_tabu_pdf():
    with open("tests/data/tabu_sample.pdf", "rb") as f:
        parser = TabuParser(f)
        rows = parser.parse()
    assert {"field": "Owner", "value": "John Doe"} in rows


def test_search_rows():
    with open("tests/data/tabu_sample.pdf", "rb") as f:
        parser = TabuParser(f)
        rows = parser.parse()
    res = parser.search("Parcel")
    assert res and res[0]["value"] == "12345"
