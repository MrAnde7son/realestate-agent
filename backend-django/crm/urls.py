from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, LeadViewSet

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(r"leads", LeadViewSet, basename="leads")

urlpatterns = router.urls
