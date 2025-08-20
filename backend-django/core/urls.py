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
    
    # Google OAuth endpoints
    path('auth/google/login/', views.auth_google_login, name='auth_google_login'),
    path('auth/google/callback/', views.auth_google_callback, name='auth_google_callback'),
    
    # Other endpoints
    path('alerts/', views.alerts, name='alerts'),
    path('listings/', views.listings, name='listings'),
    path('building-permits/', views.building_permits, name='building_permits'),
    path('building-rights/', views.building_rights, name='building_rights'),
    path('decisive-appraisals/', views.decisive_appraisals, name='decisive_appraisals'),
    path('rami-valuations/', views.rami_valuations, name='rami_valuations'),
    path('reports/', views.reports, name='reports'),
    path('tabu/', views.tabu, name='tabu'),
    path('sync-address/', views.sync_address, name='sync_address'),
]
