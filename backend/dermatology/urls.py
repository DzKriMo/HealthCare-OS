from django.urls import path
from . import views

app_name = "dermatology"

urlpatterns = [
    path("body-map/<uuid:patient_pk>/", views.BodyMapView.as_view(), name="body-map"),
    path("lesions/<uuid:patient_pk>/", views.LesionListView.as_view(), name="lesion-list"),
    path("lesion/<uuid:pk>/", views.LesionDetailView.as_view(), name="lesion-detail"),
    path("procedures/", views.ProcedureListView.as_view(), name="procedure-list"),
]
