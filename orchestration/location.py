"""Utilities for working with structured real-estate location data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class LocationQuery:
    """Immutable representation of an address query.

    The query keeps street, city and house number as structured fields while
    also providing convenient derived representations (e.g. a formatted
    address string) for collectors that still operate on free text.

    Coordinates (x_itm, y_itm) are optional and can be added when discovered
    from geocoding services like GovMap.
    """

    city: str = ""
    street: str = ""
    house_number: Optional[int] = None
    block: Optional[int] = None
    parcel: Optional[int] = None
    subparcel: Optional[int] = None
    x_itm: Optional[float] = None  # ITM X coordinate (EPSG:2039)
    y_itm: Optional[float] = None  # ITM Y coordinate (EPSG:2039)

    def __post_init__(self) -> None:
        object.__setattr__(self, "city", (self.city or "").strip())
        object.__setattr__(self, "street", (self.street or "").strip())

        number = self.house_number
        if isinstance(number, str) and number.strip().isdigit():
            number = int(number.strip())
        if not number:
            number = None
        object.__setattr__(self, "house_number", number)

    @property
    def street_with_number(self) -> str:
        """Return "street" and "house_number" if available."""

        parts = [self.street]
        if self.house_number:
            parts.append(str(self.house_number))
        return " ".join(part for part in parts if part)

    @property
    def formatted(self) -> str:
        """Return a fully formatted address string."""

        parts = [self.street]
        if self.house_number:
            parts.append(str(self.house_number))
        if self.city:
            parts.append(self.city)
        return " ".join(part for part in parts if part)

    def is_empty(self) -> bool:
        """Return True when no meaningful address component is set."""

        return not (self.street or self.city or self.house_number)

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Expose the query as serializable dictionary."""

        return {
            "city": self.city or None,
            "street": self.street or None,
            "house_number": self.house_number,
            "block": self.block,
            "parcel": self.parcel,
            "subparcel": self.subparcel,
            "x_itm": self.x_itm,
            "y_itm": self.y_itm,
        }

    def with_coordinates(
        self, x_itm: Optional[float] = None, y_itm: Optional[float] = None
    ) -> "LocationQuery":
        """Create a new LocationQuery with updated coordinates."""
        return LocationQuery(
            city=self.city,
            street=self.street,
            house_number=self.house_number,
            block=self.block,
            parcel=self.parcel,
            subparcel=self.subparcel,
            x_itm=x_itm if x_itm is not None else self.x_itm,
            y_itm=y_itm if y_itm is not None else self.y_itm,
        )


def ensure_location_query(
    location: Optional[LocationQuery] = None,
    *,
    city: str = "",
    street: str = "",
    house_number: Optional[int] = None,
    block: Optional[int] = None,
    parcel: Optional[int] = None,
    subparcel: Optional[int] = None,
    x_itm: Optional[float] = None,
    y_itm: Optional[float] = None,
) -> LocationQuery:
    """Return a :class:`LocationQuery` from either an instance or components."""

    if isinstance(location, LocationQuery):
        return LocationQuery(
            city=city or location.city,
            street=street or location.street,
            house_number=house_number
            if house_number is not None
            else location.house_number,
            block=block or location.block,
            parcel=parcel or location.parcel,
            subparcel=subparcel or location.subparcel,
            x_itm=x_itm if x_itm is not None else location.x_itm,
            y_itm=y_itm if y_itm is not None else location.y_itm,
        )
    return LocationQuery(
        city=city,
        street=street,
        house_number=house_number,
        block=block,
        parcel=parcel,
        subparcel=subparcel,
        x_itm=x_itm,
        y_itm=y_itm,
    )
