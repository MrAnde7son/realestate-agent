from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/register/', views.auth_register, name='auth_register'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/profile/', views.auth_profile, name='auth_profile'),
    path('auth/profile/update/', views.auth_update_profile, name='auth_update_profile'),
    path('auth/refresh/', views.auth_refresh, name='auth_refresh'),
    
    # Existing endpoints
    path('alerts/', views.alerts, name='alerts'),
    path('mortgage/analyze/', views.mortgage_analyze, name='mortgage_analyze'),
    path('sync-address/', views.sync_address, name='sync_address'),
    path('listings/', views.listings, name='listings'),
    path('building-permits/', views.building_permits, name='building_permits'),
    path('building-rights/', views.building_rights, name='building_rights'),
    path('decisive-appraisals/', views.decisive_appraisals, name='decisive_appraisals'),
    path('rami-valuations/', views.rami_valuations, name='rami_valuations'),
    path('tabu/', views.tabu, name='tabu'),
    path('reports/', views.reports, name='reports'),
]
