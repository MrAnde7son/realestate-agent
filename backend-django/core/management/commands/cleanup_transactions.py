from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand


def _safe_get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return None


def _normalize_city(value: Any) -> str:
    if not value:
        return ""
    normalized = str(value).strip().lower()
    return normalized.replace("-", " ").replace("–", " ").replace("־", " ")


def _address_conflicts_asset_city(address: Any, asset_city: str) -> bool:
    if not address or not asset_city:
        return False
    parts = [part.strip() for part in str(address).split(",") if part.strip()]
    if len(parts) < 3:
        return False
    asset_city_norm = _normalize_city(asset_city)
    for part in parts[1:-1]:
        part_norm = _normalize_city(part)
        if not part_norm:
            continue
        if asset_city_norm and asset_city_norm in part_norm:
            continue
        if any(char.isdigit() for char in part_norm):
            continue
        return True
    return False


def _transaction_conflicts_asset(asset, transaction) -> bool:
    raw = getattr(transaction, "raw", None) or {}
    if not isinstance(raw, dict):
        raw = {}

    asset_block = str(getattr(asset, "block", "") or "").strip().lower()
    asset_parcel = str(getattr(asset, "parcel", "") or "").strip().lower()

    tx_block = (
        str(
            _safe_get(raw, "parcel_block")
            or _safe_get(raw, "gush_num")
            or _safe_get(raw, "block")
            or ""
        )
        .strip()
        .lower()
    )
    tx_parcel = (
        str(
            _safe_get(raw, "parcel_parcel")
            or _safe_get(raw, "parcel_num")
            or _safe_get(raw, "parcel")
            or ""
        )
        .strip()
        .lower()
    )

    if asset_block and asset_parcel and tx_block and tx_parcel:
        return asset_block != tx_block or asset_parcel != tx_parcel

    asset_city = _normalize_city(getattr(asset, "city", ""))
    if asset_city:
        tx_city = _normalize_city(
            _safe_get(raw, "city") or _safe_get(raw, "settlementNameHeb")
        )
        tx_address = (
            transaction.address
            or _safe_get(raw, "address")
            or _safe_get(raw, "assetAddress")
        )
        tx_address_norm = _normalize_city(tx_address)
        if tx_city and asset_city not in tx_city:
            return True
        if not tx_city and tx_address_norm and asset_city not in tx_address_norm:
            return True
        if _address_conflicts_asset_city(tx_address, getattr(asset, "city", "")):
            return True

    return False


class Command(BaseCommand):
    help = "Remove asset-transaction links that conflict with asset location."

    def add_arguments(self, parser):
        parser.add_argument(
            "--asset-id",
            type=int,
            default=None,
            help="Limit cleanup to a specific asset id",
        )
        parser.add_argument(
            "--delete-orphans",
            action="store_true",
            help="Delete transactions that have no remaining asset links",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be removed without applying changes",
        )

    def handle(self, *args, **options):
        from core.models import AssetTransaction, RealEstateTransaction

        asset_id = options.get("asset_id")
        delete_orphans = options.get("delete_orphans")
        dry_run = options.get("dry_run")

        links = AssetTransaction.objects.select_related("asset", "transaction")
        if asset_id:
            links = links.filter(asset_id=asset_id)

        removed = 0
        seen_transactions = set()
        for link in links.iterator():
            if _transaction_conflicts_asset(link.asset, link.transaction):
                removed += 1
                seen_transactions.add(link.transaction_id)
                if not dry_run:
                    link.delete()

        orphan_deleted = 0
        if delete_orphans and seen_transactions:
            orphans = RealEstateTransaction.objects.filter(
                id__in=seen_transactions, asset_links__isnull=True
            )
            orphan_deleted = orphans.count()
            if not dry_run and orphan_deleted:
                orphans.delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Links removed: %s%s%s"
                % (
                    removed,
                    ", orphans deleted: %s" % orphan_deleted
                    if delete_orphans
                    else "",
                    " (dry run)" if dry_run else "",
                )
            )
        )
