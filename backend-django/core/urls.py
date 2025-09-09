from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views
from . import views_analytics as va
from . import views_support as vs
from .api import AssetViewSet, PermitViewSet, PlanViewSet

router = DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'permits', PermitViewSet)
router.register(r'plans', PlanViewSet)

urlpatterns = [
    # Core endpoints
    path('mortgage-analyze/', views.mortgage_analyze, name='mortgage_analyze'),
    path('sync-address/', views.sync_address, name='sync_address'),
    path('tabu/', views.tabu, name='tabu'),
    path('reports/', views.reports, name='reports'),
    path('reports/file/<str:filename>', views.report_file, name='report_file'),
    path('settings/', views.user_settings, name='user_settings'),
    path('alerts/', views.alerts, name='alerts'),
    path('alert-events/', views.alert_events, name='alert_events'),
    path('alert-test/', views.alert_test, name='alert_test'),
    path('analytics/timeseries', va.analytics_timeseries),
    path('analytics/top-failures', va.analytics_top_failures),
    path('analytics/track', va.analytics_track),
    path('analytics/page-view', va.analytics_page_view),
    path('analytics/session-end', va.analytics_session_end),
    path('onboarding-status/', views.onboarding_status, name='onboarding_status'),
    path('connect-payment/', views.connect_payment, name='connect_payment'),
    path('demo/start/', views.demo_start, name='demo_start'),
    path('support/contact', vs.support_contact),
    path('support/bug', vs.support_bug),
    path('support/consultation', vs.support_consultation),
    
    # Asset enrichment endpoints
    path('assets/', views.assets, name='assets'),
    path('assets/<int:asset_id>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:asset_id>/share-message/', views.asset_share_message, name='asset_share_message'),
    

    
    # Authentication endpoints
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/register/', views.auth_register, name='auth_register'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/profile/', views.auth_profile, name='auth_profile'),
    path('auth/update-profile/', views.auth_update_profile, name='auth_update_profile'),
    path('auth/change-password/', views.change_password, name='change_password'),
    path('auth/refresh/', views.auth_refresh, name='auth_refresh'),
    path('auth/google/login/', views.auth_google_login, name='auth_google_login'),
    path('auth/google/callback/', views.auth_google_callback, name='auth_google_callback'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('me', views.me),
    path('', include(router.urls)),
]
