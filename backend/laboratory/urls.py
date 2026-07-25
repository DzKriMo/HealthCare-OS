from django.urls import path
from . import views

app_name = "laboratory"

urlpatterns = [
    path("catalog/", views.TestCatalogView.as_view(), name="catalog"),
    path("orders/", views.LabOrderListView.as_view(), name="order-list"),
    path("orders/<uuid:pk>/", views.LabOrderDetailView.as_view(), name="order-detail"),
    path("specimens/", views.SpecimenListView.as_view(), name="specimen-list"),
    path("specimens/<uuid:pk>/transition/", views.SpecimenTransitionView.as_view(), name="specimen-transition"),
    path("results/", views.LabResultListView.as_view(), name="result-list"),
    path("results/<uuid:pk>/approve/", views.LabResultApproveView.as_view(), name="result-approve"),
    path("dashboard/", views.LabDashboardView.as_view(), name="dashboard"),
]
