from django.urls import path
from . import views

urlpatterns = [
    path('alerts/', views.alerts, name='alerts'),
    path('mortgage/analyze/', views.mortgage_analyze, name='mortgage_analyze'),
    path('sync-address/', views.sync_address, name='sync_address'),
    path('listings/', views.listings, name='listings'),
    path('analytics/property-types/', views.property_type_distribution, name='property_type_distribution'),
    path('analytics/market-activity/', views.market_activity_by_area, name='market_activity_by_area'),
    path('building-permits/', views.building_permits, name='building_permits'),
    path('building-rights/', views.building_rights, name='building_rights'),
    path('decisive-appraisals/', views.decisive_appraisals, name='decisive_appraisals'),
    path('rami-valuations/', views.rami_valuations, name='rami_valuations'),
    path('tabu/', views.tabu, name='tabu'),
    path('reports/', views.reports, name='reports'),
]
