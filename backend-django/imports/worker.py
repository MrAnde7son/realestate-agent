import csv
import io
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Tuple

from django.db import transaction

from crm.models import Contact, Lead
from core.models import Asset

from .models import ImportBatch

ENCODING_CANDIDATES = ["utf-8-sig", "cp1255", "iso-8859-8", "latin-1", "utf-8"]


@dataclass
class ImportResult:
    identifier: str
    mode: str
    status: str
    message: str = ""


def _detect_encoding(data: bytes) -> str:
    for encoding in ENCODING_CANDIDATES:
        try:
            data.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _read_csv(file_field) -> Iterable[Dict[str, str]]:
    if not file_field:
        return []
    file_field.open("rb")
    raw = file_field.read()
    file_field.close()
    encoding = _detect_encoding(raw)
    text = raw.decode(encoding, errors="replace")
    stream = io.StringIO(text)
    reader = csv.DictReader(stream)
    return list(reader)


def parse_price(val: Optional[str]) -> Optional[int]:
    if val is None:
        return None
    cleaned = str(val).replace("₪", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        as_decimal = Decimal(cleaned)
    except Exception:
        return None
    return int(as_decimal)


def parse_date(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        from dateutil import parser  # Imported lazily for tests

        return parser.parse(val, dayfirst=True)
    except Exception:
        return None


def _split_tags(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    tags = [tag.strip() for tag in str(raw).split(",") if tag.strip()]
    return tags


def _should_update(conflict_policy: str, created: bool) -> bool:
    if created:
        return True
    return conflict_policy != "skip"


def _fuzzy_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _contact_identifier(row: Dict[str, str]) -> str:
    return (
        row.get("CustomerID")
        or row.get("DisplayName")
        or row.get("PrimaryPhone")
        or "unknown"
    )


def _asset_identifier(row: Dict[str, str]) -> str:
    return row.get("PropertyID") or row.get("Street") or row.get("Phone1") or "unknown"


@transaction.atomic
def _create_or_update_contact(
    batch: ImportBatch, row: Dict[str, str], dry_run: bool, conflict_policy: str
) -> Tuple[str, ImportResult, Optional[Contact]]:
    identifier = _contact_identifier(row)
    customer_id = row.get("CustomerID")
    name = row.get("DisplayName") or ""
    phones = [
        row.get("PrimaryPhone"),
        row.get("Phone1"),
        row.get("Phone2"),
    ]
    phones = [p for p in phones if p]
    if not customer_id or (not name and not phones):
        return (
            identifier,
            ImportResult(identifier, "customer", "error", "Missing required fields"),
            None,
        )

    email = row.get("Email") or ""
    tags = _split_tags(row.get("Tags"))
    notes_parts = [row.get("Comments") or "", row.get("Description") or ""]
    notes = "\n".join(part for part in notes_parts if part)

    defaults = {
        "name": name or phones[0] if phones else "",
        "email": email,
        "notes": notes,
        "owner": batch.user,
        "tags": tags,
        "phone": phones[0] if phones else "",
        "import_batch_id": batch.id,
        "external_source": "nadlan_one",
        "external_id": customer_id,
    }

    existing_contact = Contact.objects.filter(
        external_source="nadlan_one", external_id=customer_id
    ).first()

    if dry_run:
        if existing_contact:
            status = "skipped" if conflict_policy == "skip" else "updated"
            message = (
                "Dry run - existing record would be skipped"
                if status == "skipped"
                else "Dry run - would update existing record"
            )
            return (
                identifier,
                ImportResult(identifier, "customer", status, message),
                existing_contact,
            )
        return (
            identifier,
            ImportResult(
                identifier,
                "customer",
                "inserted",
                "Dry run - would create new record",
            ),
            None,
        )

    contact = existing_contact
    created = False
    if not existing_contact:
        contact, created = Contact.objects.get_or_create(
            external_source="nadlan_one",
            external_id=customer_id,
            defaults=defaults,
        )
    else:
        contact = existing_contact

    if not created and _should_update(conflict_policy, created):
        for field, value in defaults.items():
            if field in {"owner", "import_batch_id", "external_source", "external_id"}:
                continue
            setattr(contact, field, value)
        contact.import_batch_id = batch.id
        contact.save()
    elif not created and existing_contact:
        return (
            identifier,
            ImportResult(identifier, "customer", "skipped", "Existing record"),
            contact,
        )

    status = "inserted" if created else "updated"
    return identifier, ImportResult(identifier, "customer", status), contact


@transaction.atomic
def _create_or_update_asset(
    batch: ImportBatch, row: Dict[str, str], dry_run: bool, conflict_policy: str
) -> Tuple[str, ImportResult, Optional[Asset]]:
    identifier = _asset_identifier(row)
    property_id = row.get("PropertyID")
    phones = [
        row.get("Phone1"),
        row.get("Phone2"),
        row.get("Phone3"),
    ]
    phones = [p for p in phones if p]
    has_address = any(
        row.get(key) for key in ["City", "Street", "Neighborhood", "NumHouse"]
    )
    if not property_id or (not has_address and not phones):
        return (
            identifier,
            ImportResult(identifier, "property", "error", "Missing required fields"),
            None,
        )

    price = parse_price(row.get("Price"))
    normalized_type = row.get("Type")
    evacuation = row.get("Evacuation")

    address_parts = [row.get("Street"), row.get("NumHouse"), row.get("City")]
    normalized_address = " ".join(str(part).strip() for part in address_parts if part)

    defaults = {
        "scope_type": "address",
        "city": row.get("City") or "",
        "neighborhood": row.get("Neighborhood") or "",
        "street": row.get("Street") or "",
        "number": int(row["NumHouse"])
        if row.get("NumHouse") and row.get("NumHouse").isdigit()
        else None,
        "block": row.get("Gush") or "",
        "price": price,
        "building_type": normalized_type,
        "rooms": int(row["Room"])
        if row.get("Room") and row.get("Room").isdigit()
        else None,
        "floor": int(row["Floor"])
        if row.get("Floor") and row.get("Floor").isdigit()
        else None,
        "total_floors": int(row["Floors"])
        if row.get("Floors") and row.get("Floors").isdigit()
        else None,
        "normalized_address": normalized_address or None,
        "meta": {},
        "created_by": batch.user,
        "import_batch_id": batch.id,
        "external_source": "nadlan_one",
        "external_id": property_id,
    }
    meta = {
        "owner_comment": row.get("OwnerComnt"),
        "details": row.get("Details"),
        "evacuation": evacuation,
        "priceM": row.get("PriceM"),
        "phones": phones,
        "FirstName": row.get("FirstName"),
        "LastName": row.get("LastName"),
        "FirstName2": row.get("FirstName2"),
        "LastName2": row.get("LastName2"),
    }
    defaults["meta"] = {k: v for k, v in meta.items() if v}

    existing_asset = Asset.objects.filter(
        external_source="nadlan_one", external_id=property_id
    ).first()

    if dry_run:
        if existing_asset:
            status = "skipped" if conflict_policy == "skip" else "updated"
            message = (
                "Dry run - existing record would be skipped"
                if status == "skipped"
                else "Dry run - would update existing record"
            )
            return (
                identifier,
                ImportResult(identifier, "property", status, message),
                existing_asset,
            )
        return (
            identifier,
            ImportResult(
                identifier,
                "property",
                "inserted",
                "Dry run - would create new record",
            ),
            None,
        )

    asset = existing_asset
    created = False
    if not existing_asset:
        asset, created = Asset.objects.get_or_create(
            external_source="nadlan_one",
            external_id=property_id,
            defaults=defaults,
        )
    else:
        asset = existing_asset

    if not created and _should_update(conflict_policy, created):
        for field, value in defaults.items():
            if field in {"meta"} and value:
                existing_meta = asset.meta or {}
                existing_meta.update(value)
                setattr(asset, field, existing_meta)
                continue
            if field in {"import_batch_id", "external_source", "external_id"}:
                continue
            setattr(asset, field, value)
        asset.import_batch_id = batch.id
        asset.save()
    elif not created and existing_asset:
        return (
            identifier,
            ImportResult(identifier, "property", "skipped", "Existing record"),
            asset,
        )

    status = "inserted" if created else "updated"
    return identifier, ImportResult(identifier, "property", status), asset


def _link_assets_to_contacts(
    batch: ImportBatch, contacts: List[Contact], assets: List[Asset], dry_run: bool
) -> List[ImportResult]:
    results: List[ImportResult] = []
    if not contacts or not assets:
        return results

    phone_to_contact: Dict[str, Contact] = {}
    for contact in contacts:
        if not contact:
            continue
        if contact.phone:
            phone_to_contact[contact.phone] = contact
        for tag in contact.tags or []:
            # allow additional phone tags stored as digits
            normalized_tag_phone = tag
            if normalized_tag_phone:
                phone_to_contact.setdefault(normalized_tag_phone, contact)

    for asset in assets:
        if not asset:
            continue
        phones = asset.meta.get("phones") if asset.meta else []
        matched_contact = None
        for phone in phones or []:
            if phone in phone_to_contact:
                matched_contact = phone_to_contact[phone]
                break
        if not matched_contact:
            owner_name = (
                " ".join(
                    part
                    for part in [
                        asset.meta.get("FirstName"),
                        asset.meta.get("LastName"),
                    ]
                    if part
                )
                if asset.meta
                else None
            )
            for contact in contacts:
                ratio = _fuzzy_ratio(contact.name or "", owner_name or "")
                if ratio >= 0.9:
                    matched_contact = contact
                    break
        if matched_contact and not dry_run:
            lead, created = Lead.objects.get_or_create(
                contact=matched_contact, asset=asset
            )
            if created:
                results.append(
                    ImportResult(
                        str(asset.external_id or asset.pk),
                        "link",
                        "inserted",
                        f"Linked to contact {matched_contact.id}",
                    )
                )
    return results


def process_csvs(
    batch: ImportBatch,
    mode: str,
    dry_run: bool,
    conflict_policy: str,
    enable_linking: bool,
):
    customer_rows = _read_csv(batch.customers_csv)
    property_rows = _read_csv(batch.properties_csv)

    summary = defaultdict(int)
    row_results: List[ImportResult] = []
    processed_contacts: List[Contact] = []
    processed_assets: List[Asset] = []

    if mode == ImportBatch.MODE_CUSTOMERS or customer_rows:
        for row in customer_rows:
            summary["processed"] += 1
            identifier, result, contact = _create_or_update_contact(
                batch, row, dry_run, conflict_policy
            )
            row_results.append(result)
            if result.status == "error":
                summary["errors"] += 1
            elif result.status == "skipped":
                summary["skipped"] += 1
            elif result.status == "inserted":
                summary["inserted"] += 1
            elif result.status == "updated":
                summary["updated"] += 1
            if contact:
                processed_contacts.append(contact)

    if mode == ImportBatch.MODE_PROPERTIES or property_rows:
        for row in property_rows:
            summary["processed"] += 1
            identifier, result, asset = _create_or_update_asset(
                batch, row, dry_run, conflict_policy
            )
            row_results.append(result)
            if result.status == "error":
                summary["errors"] += 1
            elif result.status == "skipped":
                summary["skipped"] += 1
            elif result.status == "inserted":
                summary["inserted"] += 1
            elif result.status == "updated":
                summary["updated"] += 1
            if asset:
                processed_assets.append(asset)

    if enable_linking and processed_contacts and processed_assets:
        linking_results = _link_assets_to_contacts(
            batch, processed_contacts, processed_assets, dry_run
        )
        row_results.extend(linking_results)
        summary["linked"] += len(linking_results)

    csv_output = io.StringIO()
    fieldnames = ["mode", "identifier", "status", "message"]
    writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
    writer.writeheader()
    for item in row_results:
        writer.writerow(
            {
                "mode": item.mode,
                "identifier": item.identifier,
                "status": item.status,
                "message": item.message,
            }
        )

    json_report = json.dumps(
        [
            {
                "mode": item.mode,
                "identifier": item.identifier,
                "status": item.status,
                "message": item.message,
            }
            for item in row_results
        ],
        ensure_ascii=False,
        indent=2,
    )

    return {
        "summary": dict(summary),
        "csv_report": csv_output.getvalue(),
        "json_report": json_report,
    }
