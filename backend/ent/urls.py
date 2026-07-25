from django.urls import path
from . import views

app_name = "ent"

urlpatterns = [
    path("audiology/", views.AudiologyListView.as_view(), name="audiology-list"),
    path("endoscopy/", views.EndoscopyListView.as_view(), name="endoscopy-list"),
]
