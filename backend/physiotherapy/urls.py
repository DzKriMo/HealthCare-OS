from django.urls import path; from . import views
app_name = "physiotherapy"
urlpatterns = [path("sessions/", views.PhysioSessionListView.as_view(), name="session-list")]
