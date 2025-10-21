from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from orchestration.location import LocationQuery

logger = logging.getLogger(__name__)

_DEFAULT_MAX_NEW_ASSETS = int(os.getenv("DATA_PIPELINE_AUTO_ASSET_LIMIT", "10"))


@dataclass(frozen=True)
class AddressCandidate:
    location: LocationQuery
    source: str
    scope_type: str = "address"
    raw_address: Optional[str] = None

    @property
    def street(self) -> str:
        return self.location.street

    @property
    def number(self) -> Optional[int]:
        return self.location.house_number

    @property
    def city(self) -> str:
        return self.location.city

    def key(self) -> Tuple[str, ...]:
        if self.scope_type == "parcel":
            return (
                "parcel",
                _normalize_text(self.location.city).lower(),
                _normalize_text(self.location.block).lower(),
                _normalize_text(self.location.parcel).lower(),
                _normalize_text(self.location.subparcel).lower(),
            )
        return (
            "address",
            _normalize_text(self.location.city).lower(),
            _normalize_text(self.location.street).lower(),
            int(self.location.house_number or 0),
        )


@dataclass(frozen=True)
class CandidateComponents:
    scope_type: str
    street: str = ""
    number: Optional[int] = None
    city: str = ""
    raw_address: Optional[str] = None
    block: Optional[str] = None
    parcel: Optional[str] = None
    subparcel: Optional[str] = None


def auto_expand_related_assets(
    asset_id: Optional[int],
    listings: Sequence[Dict[str, Any]] | None = None,
    govmap_data: Dict[str, Any] | None = None,
    gis_data: Dict[str, Any] | None = None,
    gov_data: Dict[str, Any] | None = None,
    plans: Sequence[Dict[str, Any]] | None = None,
    mavat_plans: Sequence[Dict[str, Any]] | None = None,
    handasa_archive: Sequence[Dict[str, Any]] | None = None,
    max_new_assets: Optional[int] = None,
) -> List[int]:
    """Create additional assets discovered in collected datasets.

    Returns a list of newly created asset IDs (if any).
    """
    if not asset_id:
        return []

    try:
        from django.apps import apps
        from django.db import transaction
        from django.utils import timezone

        Asset = apps.get_model("core", "Asset")  # type: ignore[arg-type]
    except Exception:  # pragma: no cover - Django not configured
        logger.debug("Skipping auto asset expansion; Django models unavailable")
        return []

    try:
        base_asset = Asset.objects.select_related("created_by").get(id=asset_id)
    except Asset.DoesNotExist:
        logger.warning("Cannot auto expand assets; base asset %s not found", asset_id)
        return []

    fallback_city = base_asset.city or ""
    max_assets = max_new_assets or _DEFAULT_MAX_NEW_ASSETS
    if max_assets <= 0:
        return []

    datasets: List[Tuple[str, Any]] = [
        ("yad2_listing", listings or []),
        ("govmap", govmap_data or {}),
        ("gis", gis_data or {}),
        ("gov_decisive", (gov_data or {}).get("decisive", [])),
        ("gov_transactions", (gov_data or {}).get("transactions", [])),
        ("rami", plans or []),
        ("mavat", mavat_plans or []),
        ("handasa", handasa_archive or []),
    ]

    candidates: List[AddressCandidate] = []
    seen_candidate_keys: set[Tuple[str, ...]] = set()
    for source_name, payload in datasets:
        for candidate in _extract_candidates(payload, source_name, fallback_city=fallback_city):
            key = candidate.key()
            if key in seen_candidate_keys:
                continue
            seen_candidate_keys.add(key)
            candidates.append(candidate)
            if len(candidates) >= max_assets * 3:
                # guardrail: stop scanning once we have plenty of options
                break

    if not candidates:
        return []

    created_asset_ids: List[int] = []
    created_keys: set[Tuple[str, ...]] = set(_candidate_keys_from_asset(base_asset))

    for candidate in candidates:
        if len(created_asset_ids) >= max_assets:
            break

        key = candidate.key()
        if key in created_keys:
            continue

        if _asset_exists(candidate, Asset):
            created_keys.add(key)
            continue

        user = getattr(base_asset, "created_by", None)
        if user and hasattr(user, "can_create_asset") and not user.can_create_asset():
            logger.info(
                "Skipping auto creation for %s %s %s - user %s asset limit reached",
                candidate.street,
                candidate.number,
                candidate.city,
                user.id if hasattr(user, "id") else "?",
            )
            break

        try:
            with transaction.atomic():
                if candidate.scope_type == "parcel":
                    new_asset = Asset.objects.create(
                        scope_type="parcel",
                        city=candidate.location.city or fallback_city,
                        block=candidate.location.block,
                        parcel=candidate.location.parcel,
                        subparcel=candidate.location.subparcel,
                        normalized_address=_format_parcel_label(
                            candidate.location.block,
                            candidate.location.parcel,
                            candidate.location.subparcel,
                            candidate.location.city or fallback_city,
                        ),
                        status="pending",
                        meta={
                            "auto_created": True,
                            "auto_created_from": asset_id,
                            "source": candidate.source,
                            "raw_address": candidate.raw_address,
                            "scope_type": "parcel",
                            "location_hint": candidate.location.to_dict(),
                            "auto_created_at": timezone.now().isoformat(),
                        },
                        created_by=user,
                        last_updated_by=user,
                    )
                else:
                    new_asset = Asset.objects.create(
                        scope_type="address",
                        city=candidate.location.city or fallback_city,
                        street=candidate.location.street,
                        number=candidate.location.house_number,
                        block=candidate.location.block,
                        parcel=candidate.location.parcel,
                        subparcel=candidate.location.subparcel,
                        normalized_address=_format_normalized_address(
                            candidate.location.street,
                            int(candidate.location.house_number or 0),
                            candidate.location.city or fallback_city,
                        ),
                        status="pending",
                        meta={
                            "auto_created": True,
                            "auto_created_from": asset_id,
                            "source": candidate.source,
                            "raw_address": candidate.raw_address,
                            "scope_type": "address",
                            "location_hint": candidate.location.to_dict(),
                            "auto_created_at": timezone.now().isoformat(),
                        },
                        created_by=user,
                        last_updated_by=user,
                    )
        except Exception as exc:  # pragma: no cover - defensive persistence
            logger.warning(
                "Failed to auto-create asset for %s %s %s: %s",
                candidate.street,
                candidate.number,
                candidate.city,
                exc,
            )
            continue

        created_asset_ids.append(new_asset.id)
        created_keys.update(_candidate_keys_from_asset(new_asset))
        _trigger_pipeline_for_asset(new_asset.id)

    return created_asset_ids


def _candidate_keys_from_asset(asset: Any) -> List[Tuple[str, ...]]:
    city = _normalize_text(getattr(asset, "city", "")).lower()
    street = _normalize_text(getattr(asset, "street", "")).lower()
    block = _normalize_text(getattr(asset, "block", "")).lower()
    parcel = _normalize_text(getattr(asset, "parcel", "")).lower()
    subparcel = _normalize_text(getattr(asset, "subparcel", "")).lower()

    try:
        number = int(getattr(asset, "number", 0) or 0)
    except Exception:
        number = 0

    keys: List[Tuple[str, ...]] = []
    if street or number:
        keys.append(("address", city, street, number))
    if block or parcel:
        keys.append(("parcel", city, block, parcel, subparcel))
    return keys


def _asset_exists(candidate: AddressCandidate, AssetModel: Any) -> bool:
    try:
        queryset = AssetModel.objects.all()
        if candidate.scope_type == "parcel":
            if candidate.location.block:
                queryset = queryset.filter(block__iexact=candidate.location.block.strip())
            if candidate.location.parcel:
                queryset = queryset.filter(parcel__iexact=candidate.location.parcel.strip())
            if candidate.location.subparcel:
                queryset = queryset.filter(subparcel__iexact=candidate.location.subparcel.strip())
            if candidate.city:
                queryset = queryset.filter(city__iexact=candidate.city.strip())
            return queryset.exists()

        return queryset.filter(
            street__iexact=candidate.street.strip(),
            number=candidate.number,
            city__iexact=candidate.city.strip(),
        ).exists()
    except Exception:
        return True  # fail-safe to avoid duplicates if query fails


def _extract_candidates(
    payload: Any,
    source: str,
    fallback_city: str = "",
) -> Iterator[AddressCandidate]:
    if not payload:
        return

    for mapping in _iter_mappings(payload):
        components = _extract_address_components(mapping, fallback_city=fallback_city)
        if not components:
            continue
        candidate_location = LocationQuery(
            street=components.street,
            house_number=components.number,
            city=components.city,
            block=components.block,
            parcel=components.parcel,
            subparcel=components.subparcel,
        )
        yield AddressCandidate(
            location=candidate_location,
            source=source,
            scope_type=components.scope_type,
            raw_address=components.raw_address,
        )


def _iter_mappings(obj: Any) -> Iterator[Dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _iter_mappings(value)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            yield from _iter_mappings(item)


_STREET_TOKENS = {
    "street",
    "streetname",
    "streetheb",
    "streetdesc",
    "streettext",
    "addrstreet",
    "sreet",
}
_NUMBER_TOKENS = {
    "housenumber",
    "number",
    "streetnumber",
    "streetno",
    "streetnum",
    "homenumber",
    "home_number",
    "hn",
}
_CITY_TOKENS = {
    "city",
    "cityname",
    "settlement",
    "municipality",
    "yishuv",
    "locality",
    "town",
    "cityheb",
}
_ADDRESS_TOKENS = {
    "address",
    "fulladdress",
    "addr",
    "addressline",
    "address_text",
}


def _extract_address_components(
    mapping: Dict[str, Any],
    fallback_city: str = "",
) -> Optional[CandidateComponents]:
    street_value = _find_first_by_token(mapping, _STREET_TOKENS)
    number_value = _find_first_by_token(mapping, _NUMBER_TOKENS)
    city_value = _find_first_by_token(mapping, _CITY_TOKENS) or fallback_city
    address_value = _find_first_by_token(mapping, _ADDRESS_TOKENS)
    block_value = _find_first_by_token(mapping, {"block", "gush", "blocknumber", "block_id"})
    parcel_value = _find_first_by_token(mapping, {"parcel", "helka", "parcelnumber", "parcel_id"})
    subparcel_value = _find_first_by_token(mapping, {"subparcel", "tathelka", "sub_parcel"})

    street = _normalize_text(street_value)
    city = _normalize_text(city_value) or _normalize_text(fallback_city)
    number = _normalize_number(number_value)
    block = _normalize_text(block_value) or None
    parcel = _normalize_text(parcel_value) or None
    subparcel = _normalize_text(subparcel_value) or None

    if street and number and city:
        return CandidateComponents(
            scope_type="address",
            street=street,
            number=number,
            city=city,
            raw_address=_normalize_text(address_value) or None,
            block=block,
            parcel=parcel,
            subparcel=subparcel,
        )

    parsed: Optional[Tuple[str, int, str]] = None
    if isinstance(address_value, str):
        parsed = _parse_address_string(address_value, fallback_city=fallback_city)
    if parsed:
        street, number, city = parsed
        return CandidateComponents(
            scope_type="address",
            street=street,
            number=number,
            city=city,
            raw_address=address_value.strip(),
            block=block,
            parcel=parcel,
            subparcel=subparcel,
        )

    if block and parcel and city:
        return CandidateComponents(
            scope_type="parcel",
            street=street,
            number=number,
            city=city,
            raw_address=_normalize_text(address_value) or None,
            block=block,
            parcel=parcel,
            subparcel=subparcel,
        )

    return None


def _find_first_by_token(obj: Any, tokens: Iterable[str]) -> Optional[Any]:
    token_set = {_normalize_token(t) for t in tokens}
    return _find_in_structure(obj, token_set)


def _find_in_structure(obj: Any, token_set: set[str]) -> Optional[Any]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized_key = _normalize_token(str(key))
            if normalized_key in token_set:
                if value not in (None, "", []):
                    return value
            found = _find_in_structure(value, token_set)
            if found not in (None, "", []):
                return found
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            found = _find_in_structure(item, token_set)
            if found not in (None, "", []):
                return found
    return None


def _parse_address_string(address: str, fallback_city: str = "") -> Optional[Tuple[str, int, str]]:
    if not address or not isinstance(address, str):
        return None
    cleaned = address.replace(",", " ").strip()
    match = re.search(r"(.+?)\s*(\d+)\s*(.*)", cleaned)
    if not match:
        return None
    street_raw, number_str, city_raw = match.groups()
    street = _normalize_text(street_raw)
    number = _normalize_number(number_str)
    city = _normalize_text(city_raw) or _normalize_text(fallback_city)
    if street and number and city:
        return street, number, city
    return None


def _normalize_number(value: Any) -> Optional[int]:
    if value in (None, "", []):
        return None
    if isinstance(value, dict):
        flattened = _normalize_text(value)
        return _normalize_number(flattened)
    if isinstance(value, (list, tuple, set)):
        for item in value:
            number = _normalize_number(item)
            if number is not None:
                return number
        return None
    if isinstance(value, (int, float)):
        if value <= 0:
            return None
        return int(value)
    if isinstance(value, str):
        match = re.search(r"(\d+)", value)
        if match:
            try:
                number = int(match.group(1))
                if number > 0:
                    return number
            except ValueError:
                return None
    return None


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("text", "value", "name", "desc", "description", "label"):
            if key in value:
                normalized = _normalize_text(value[key])
                if normalized:
                    return normalized
        for val in value.values():
            normalized = _normalize_text(val)
            if normalized:
                return normalized
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            normalized = _normalize_text(item)
            if normalized:
                return normalized
        return ""
    if isinstance(value, (int, float)):
        return str(value).strip()
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalize_token(token: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", token).lower()


def _format_normalized_address(street: str, number: int, city: str) -> str:
    parts = [_normalize_text(street), str(number)]
    city_norm = _normalize_text(city)
    if city_norm:
        parts.append(city_norm)
    return " ".join(part for part in parts if part)


def _format_parcel_label(
    block: Optional[str],
    parcel: Optional[str],
    subparcel: Optional[str],
    city: str,
) -> str:
    parts: List[str] = []
    block_norm = _normalize_text(block)
    parcel_norm = _normalize_text(parcel)
    subparcel_norm = _normalize_text(subparcel)
    if block_norm:
        parts.append(f"Block {block_norm}")
    if parcel_norm:
        parts.append(f"Parcel {parcel_norm}")
    if subparcel_norm:
        parts.append(f"Subparcel {subparcel_norm}")
    city_norm = _normalize_text(city)
    if city_norm:
        parts.append(city_norm)
    return " ".join(part for part in parts if part)


def _trigger_pipeline_for_asset(asset_id: int) -> None:
    try:
        from django.conf import settings
        from core.tasks import run_data_pipeline

        broker = getattr(settings, "CELERY_BROKER_URL", None)
        if broker:
            run_data_pipeline.delay(asset_id)  # type: ignore[attr-defined]
            return

        def _run_sync() -> None:
            try:
                run_data_pipeline(asset_id)
            except Exception:
                logger.exception("Auto-created asset %s enrichment failed", asset_id)

        thread = threading.Thread(target=_run_sync, name=f"auto-enrich-{asset_id}", daemon=True)
        thread.start()
    except Exception:  # pragma: no cover - best effort scheduling
        logger.exception("Failed to schedule enrichment for auto-created asset %s", asset_id)
