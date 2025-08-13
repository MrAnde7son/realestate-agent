import pytest
from yad2.core.parameters import Yad2SearchParameters


def test_set_parameter_numeric_and_boolean():
    params = Yad2SearchParameters()
    params.set_parameter('maxPrice', '5000')
    assert params.parameters['maxPrice'] == 5000

    params.set_parameter('elevator', 'yes')
    assert params.parameters['elevator'] == 1

    params.set_parameter('elevator', 'no')
    assert params.parameters['elevator'] == 0

    params.set_parameter('elevator', '2')
    assert params.parameters['elevator'] == 2

    params.set_parameter('maxPrice', '')
    assert params.parameters['maxPrice'] is None

    params.set_parameter('street', 'Main')
    assert params.parameters['street'] == 'Main'


def test_set_parameter_invalid_and_unknown():
    params = Yad2SearchParameters()
    with pytest.raises(ValueError):
        params.set_parameter('maxPrice', 'not-a-number')

    with pytest.raises(ValueError):
        params.set_parameter('unknown', 'value')


def test_to_dict_and_empty_build_url():
    params = Yad2SearchParameters()
    assert params.to_dict() == {}
    assert (
        params.build_url() == "https://www.yad2.co.il/realestate/forsale"
    )
