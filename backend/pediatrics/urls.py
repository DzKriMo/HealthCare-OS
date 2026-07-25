from django.urls import path
from . import views

app_name = "pediatrics"

urlpatterns = [
    path("growth/", views.GrowthListView.as_view(), name="growth-list"),
    path("vaccinations/", views.VaxScheduleListView.as_view(), name="vax-schedule"),
    path("milestones/", views.MilestoneListView.as_view(), name="milestone-list"),
    path("dashboard/", views.PedsDashboardView.as_view(), name="dashboard"),
]
