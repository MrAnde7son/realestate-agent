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
    """

    city: str = ""
    street: str = ""
    house_number: Optional[int] = None
    block: Optional[str] = None
    parcel: Optional[str] = None
    subparcel: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "city", (self.city or "").strip())
        object.__setattr__(self, "street", (self.street or "").strip())

        number = self.house_number
        if isinstance(number, str) and number.strip().isdigit():
            number = int(number.strip())
        if not number:
            number = None
        object.__setattr__(self, "house_number", number)

        for field_name in ("block", "parcel", "subparcel"):
            value = getattr(self, field_name)
            normalized = (value or "").strip() or None
            object.__setattr__(self, field_name, normalized)

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
        }


def ensure_location_query(
    location: Optional[LocationQuery] = None,
    *,
    city: str = "",
    street: str = "",
    house_number: Optional[int] = None,
    block: Optional[str] = None,
    parcel: Optional[str] = None,
    subparcel: Optional[str] = None,
) -> LocationQuery:
    """Return a :class:`LocationQuery` from either an instance or components."""

    if isinstance(location, LocationQuery):
        return LocationQuery(
            city=city or location.city,
            street=street or location.street,
            house_number=house_number if house_number is not None else location.house_number,
            block=block or location.block,
            parcel=parcel or location.parcel,
            subparcel=subparcel or location.subparcel,
        )
    return LocationQuery(
        city=city,
        street=street,
        house_number=house_number,
        block=block,
        parcel=parcel,
        subparcel=subparcel,
    )
