"""Document URLs."""
from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="document-list"),
    path("<uuid:pk>/", views.DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:pk>/download/", views.DocumentDownloadView.as_view(), name="document-download"),
    path("signatures/", views.SignatureListView.as_view(), name="signature-list"),
]
