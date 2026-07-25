from django.urls import path
from . import views

app_name = "reporting"

urlpatterns = [
    path("definitions/", views.ReportDefinitionListView.as_view(), name="report-definitions"),
    path("run/", views.ReportRunView.as_view(), name="report-run"),
    path("widgets/", views.DashboardWidgetListView.as_view(), name="dashboard-widgets"),
    path("dashboard/", views.DashboardDataView.as_view(), name="dashboard-data"),
]
