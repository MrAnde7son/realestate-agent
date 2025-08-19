from utils.tabu_parser import parse_tabu_pdf, search_rows


def test_parse_tabu_pdf():
    with open('tests/data/tabu_sample.pdf', 'rb') as f:
        rows = parse_tabu_pdf(f)
    assert {'field': 'Owner', 'value': 'John Doe'} in rows


def test_search_rows():
    with open('tests/data/tabu_sample.pdf', 'rb') as f:
        rows = parse_tabu_pdf(f)
    res = search_rows(rows, 'Parcel')
    assert res and res[0]['value'] == '12345'
