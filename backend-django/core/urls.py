from django.urls import path
from . import views

urlpatterns = [
    path('alerts/', views.alerts, name='alerts'),
    path('mortgage/analyze/', views.mortgage_analyze, name='mortgage_analyze'),
    path('listings/', views.listings, name='listings'),
    path('building-permits/', views.building_permits, name='building_permits'),
    path('building-rights/', views.building_rights, name='building_rights'),
    path('decisive-appraisals/', views.decisive_appraisals, name='decisive_appraisals'),
    path('rami-valuations/', views.rami_valuations, name='rami_valuations'),
]
