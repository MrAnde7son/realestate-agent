"""Helper functions for transitional asset relationships."""

from django.db.models import Q


def asset_documents_all(asset):
    from ..models import Document

    return Document.objects.filter(Q(asset=asset) | Q(assets=asset)).distinct()


def asset_transactions_all(asset):
    from ..models import RealEstateTransaction

    return RealEstateTransaction.objects.filter(
        Q(asset=asset) | Q(assets=asset)
    ).distinct()


def asset_permits_all(asset):
    from ..models import Permit

    return Permit.objects.filter(Q(asset=asset) | Q(assets=asset)).distinct()


def asset_plans_all(asset):
    from ..models import Plan

    return Plan.objects.filter(Q(asset=asset) | Q(assets=asset)).distinct()


def asset_listings_all(asset):
    from ..models import Listing

    return Listing.objects.filter(asset_links__asset=asset).distinct()
