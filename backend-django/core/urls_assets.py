"""Shared URL patterns for asset-related endpoints.

These patterns are included both under the primary ``/api`` prefix and
at the root of the service for backward compatibility with legacy
clients that expect asset routes without the ``/api`` prefix.
"""

from django.urls import path

from . import views
from . import views_documents as vd

urlpatterns = [
    # Declare collection endpoints before ID-based routes to avoid conflicts.
    path('', views.assets, name='assets'),
    path('bulk-action', views.assets_bulk_action, name='assets_bulk_action'),

    # Asset detail and enrichment routes
    path('<int:asset_id>', views.asset_detail, name='asset_detail'),
    path(
        '<int:asset_id>/appraisal',
        views.asset_appraisal,
        name='asset_appraisal',
    ),
    path(
        '<int:asset_id>/transactions',
        views.asset_transactions,
        name='asset_transactions',
    ),
    path('<int:asset_id>/permits', views.asset_permits, name='asset_permits'),
    path('<int:asset_id>/plans', views.asset_plans, name='asset_plans'),
    path(
        '<int:asset_id>/rights',
        vd.AssetRightsView.as_view(),
        name='asset_rights',
    ),
    path(
        '<int:asset_id>/share-message',
        views.asset_share_message,
        name='asset_share_message',
    ),
    path(
        '<int:asset_id>/landing-page',
        views.asset_landing_page,
        name='asset_landing_page',
    ),
    path(
        '<int:asset_id>/watch',
        views.asset_watch,
        name='asset_watch',
    ),
    path(
        '<int:asset_id>/listings',
        views.asset_listings,
        name='asset_listings',
    ),
    path('<int:asset_id>/sync', views.sync_asset, name='sync_asset'),

    # Document management
    path(
        '<int:asset_id>/documents',
        vd.DocumentListView.as_view(),
        name='asset_documents',
    ),
    path(
        '<int:asset_id>/documents/upload',
        vd.DocumentUploadView.as_view(),
        name='document_upload',
    ),
    path(
        '<int:asset_id>/documents/<int:document_id>',
        vd.DocumentDetailView.as_view(),
        name='document_detail',
    ),
    path(
        '<int:asset_id>/documents/<int:document_id>/download',
        vd.DocumentDownloadView.as_view(),
        name='document_download',
    ),
    path(
        '<int:asset_id>/documents/migrate-meta',
        vd.create_document_from_meta,
        name='migrate_meta_documents',
    ),

    # Attribution
    path(
        '<int:asset_id>/contributions',
        views.asset_contributions,
        name='asset_contributions',
    ),
    path(
        '<int:asset_id>/add-contribution',
        views.add_contribution,
        name='add_contribution',
    ),
]
