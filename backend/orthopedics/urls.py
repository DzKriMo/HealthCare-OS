from django.urls import path
from . import views

app_name = "orthopedics"

urlpatterns = [
    path("joints/", views.JointListView.as_view(), name="joint-list"),
    path("fractures/", views.FractureListView.as_view(), name="fracture-list"),
    path("physio/", views.PhysioListView.as_view(), name="physio-list"),
]
