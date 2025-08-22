from django.urls import path
from . import views

urlpatterns = [
    # Core endpoints
    path('mortgage-analyze/', views.mortgage_analyze, name='mortgage_analyze'),
    path('sync-address/', views.sync_address, name='sync_address'),
    path('tabu/', views.tabu, name='tabu'),
    path('reports/', views.reports, name='reports'),
    path('alerts/', views.alerts, name='alerts'),
    
    # Asset enrichment endpoints
    path('assets/', views.assets, name='assets'),
    path('assets/<int:asset_id>/', views.asset_detail, name='asset_detail'),
    

    
    # Authentication endpoints
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/register/', views.auth_register, name='auth_register'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/profile/', views.auth_profile, name='auth_profile'),
    path('auth/update-profile/', views.auth_update_profile, name='auth_update_profile'),
    path('auth/refresh/', views.auth_refresh, name='auth_refresh'),
    path('auth/google/login/', views.auth_google_login, name='auth_google_login'),
    path('auth/google/callback/', views.auth_google_callback, name='auth_google_callback'),
]
