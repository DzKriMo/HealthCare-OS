from django.urls import path; from . import views
app_name = "oncology"
urlpatterns = [path("staging/", views.StagingListView.as_view(), name="staging-list"), path("chemo/", views.ChemoListView.as_view(), name="chemo-list"), path("markers/", views.TumorMarkerView.as_view(), name="marker-list")]
