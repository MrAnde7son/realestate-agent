from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r"deals", views.DealViewSet, basename="workspace-deal")
router.register(
    r"negotiations", views.NegotiationViewSet, basename="workspace-negotiation"
)
router.register(r"offers", views.OfferViewSet, basename="workspace-offer")
router.register(
    r"documents", views.DocumentViewSet, basename="workspace-document"
)
router.register(
    r"legal/cases", views.LegalCaseViewSet, basename="workspace-legalcase"
)
router.register(r"tasks", views.TaskViewSet, basename="workspace-task")
router.register(
    r"appraisals", views.AppraisalViewSet, basename="workspace-appraisal"
)
router.register(
    r"plan-sets", views.PlanSetViewSet, basename="workspace-planset"
)
router.register(
    r"mortgages",
    views.MortgageApplicationViewSet,
    basename="workspace-mortgage",
)
router.register(
    r"mortgage-offers",
    views.MortgageOfferViewSet,
    basename="workspace-mortgageoffer",
)
router.register(
    r"audit-logs", views.AuditLogViewSet, basename="workspace-auditlog"
)

urlpatterns = [
    path(
        "deals/<int:asset_id>",
        views.DealCreateView.as_view(),
        name="workspace-deal-create",
    ),
    path(
        "negotiations/<int:deal_id>",
        views.NegotiationCreateView.as_view(),
        name="workspace-negotiation-create",
    ),
    path("", include(router.urls)),
]
