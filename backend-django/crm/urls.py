from rest_framework.routers import DefaultRouter
from .views import (
    ContactViewSet,
    LeadViewSet,
    ContactTaskViewSet,
    ContactMeetingViewSet,
    ContactInteractionViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register("contacts", ContactViewSet, basename="contacts")
router.register("leads", LeadViewSet, basename="leads")
router.register("tasks", ContactTaskViewSet, basename="contact-tasks")
router.register("meetings", ContactMeetingViewSet, basename="contact-meetings")
router.register(
    "interactions", ContactInteractionViewSet, basename="contact-interactions"
)

urlpatterns = router.urls
