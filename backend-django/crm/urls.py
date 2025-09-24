from rest_framework.routers import DefaultRouter
from .views import (
    ContactViewSet,
    LeadViewSet,
    ContactTaskViewSet,
    ContactMeetingViewSet,
    ContactInteractionViewSet,
)

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(r"leads", LeadViewSet, basename="leads")
router.register(r"tasks", ContactTaskViewSet, basename="contact-tasks")
router.register(r"meetings", ContactMeetingViewSet, basename="contact-meetings")
router.register(r"interactions", ContactInteractionViewSet, basename="contact-interactions")

urlpatterns = router.urls
