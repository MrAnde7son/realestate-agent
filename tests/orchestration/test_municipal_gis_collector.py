import pytest

from orchestration.collectors.municipal_gis import (
    MultiCityGISCollector,
    MunicipalGisAdapter,
    TelAvivMunicipalGisAdapter,
)
from orchestration.location import LocationQuery


class _FakeAdapter(MunicipalGisAdapter):
    def __init__(self, name: str, supported_cities):
        super().__init__()
        self._name = name
        self.supported_cities = supported_cities

    def collect(self, location: LocationQuery):
        return {"adapter": self._name, "city": location.city}


class _StubCollector:
    def __init__(self, name: str):
        self.name = name

    def collect(self, location: LocationQuery, **_kwargs):
        return {"adapter": self.name, "city": location.city}


def test_multi_city_raises_for_unknown_city():
    collector = MultiCityGISCollector(adapters=[TelAvivMunicipalGisAdapter(collector=_StubCollector("ta"))])

    with pytest.raises(ValueError):
        collector.collect(LocationQuery(city="מודיעין"))


@pytest.mark.parametrize(
    "city_variant",
    ["Tel Aviv", "tel aviv", "תל אביב", "תל אביב - יפו"],
)
def test_tel_aviv_adapter_city_normalization(city_variant):
    adapter = TelAvivMunicipalGisAdapter(collector=None)

    assert adapter.supports(city_variant)

