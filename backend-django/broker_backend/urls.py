from django.contrib import admin
from django.urls import include, path, re_path
from core import views as core_views
from notifications.views import resend_webhook
from api_mcp.views import MCPAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^mcp/?$', MCPAPIView.as_view(), name='api-mcp'),
    path('api/', include('core.urls')),
    path('api/crm/', include('crm.urls')),
    path('api/imports/', include('imports.urls')),
    path('api/deal-workspace/', include('deal_workspace.urls')),
    path(
        'r/<str:token>/',
        core_views.asset_share_read_only,
        name='asset_share_read_only',
    ),
    path('webhooks/resend/', resend_webhook, name='resend_webhook'),
]
