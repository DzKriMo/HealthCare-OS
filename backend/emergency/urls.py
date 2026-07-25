from django.urls import path; from . import views
app_name = "emergency"
urlpatterns = [path("visits/", views.ERVisitListView.as_view(), name="er-list")]
