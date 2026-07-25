from django.urls import path; from . import views
app_name = "dialysis"
urlpatterns = [path("sessions/", views.DialysisSessionListView.as_view(), name="session-list")]
