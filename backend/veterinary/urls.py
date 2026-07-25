from django.urls import path; from . import views
app_name = "veterinary"
urlpatterns = [path("animal/<uuid:patient_pk>/", views.AnimalRecordView.as_view(), name="animal-record"), path("rabies/", views.RabiesCertListView.as_view(), name="rabies-list")]
