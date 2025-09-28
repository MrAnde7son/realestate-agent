from django.contrib import admin
from django.urls import include, path
from core import views as core_views
from notifications.views import resend_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/crm/', include('crm.urls')),
    path('r/<str:token>', core_views.asset_share_read_only, name='asset_share_read_only'),
    path('webhooks/resend', resend_webhook, name='resend_webhook'),
]
