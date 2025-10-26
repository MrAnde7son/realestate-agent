from django.urls import path

from .views import ImportBatchDetailView, ImportBatchListView, NadlanOneImportView

urlpatterns = [
    path("nadlanone", NadlanOneImportView.as_view(), name="nadlanone-import"),
    path("<uuid:batch_id>", ImportBatchDetailView.as_view(), name="import-batch-detail"),
    path("", ImportBatchListView.as_view(), name="import-batch-list"),
]
