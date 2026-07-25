from django.urls import path
from . import views

app_name = "gynecology"

urlpatterns = [
    path("ob-history/<uuid:patient_pk>/", views.OBHistoryView.as_view(), name="ob-history"),
    path("pap/", views.PapSmearListView.as_view(), name="pap-list"),
    path("antenatal/", views.AntenatalListView.as_view(), name="antenatal-list"),
]
