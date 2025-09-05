from django.contrib import admin
from django.urls import include, path
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('r/<str:token>', core_views.asset_share_read_only, name='asset_share_read_only'),
]
