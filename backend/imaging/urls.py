from django.urls import path
from . import views

app_name = "imaging"

urlpatterns = [
    path("studies/", views.StudyListView.as_view(), name="study-list"),
    path("studies/<uuid:pk>/", views.StudyDetailView.as_view(), name="study-detail"),
    path("reports/", views.ReportListView.as_view(), name="report-list"),
    path("reports/<uuid:pk>/sign/", views.ReportSignView.as_view(), name="report-sign"),
    path("dashboard/", views.ImagingDashboardView.as_view(), name="dashboard"),
]
