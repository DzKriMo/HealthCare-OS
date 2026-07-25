from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("items/", views.ItemListView.as_view(), name="item-list"),
    path("items/<uuid:pk>/", views.ItemDetailView.as_view(), name="item-detail"),
    path("stock/adjust/", views.StockAdjustmentView.as_view(), name="stock-adjust"),
    path("stock/movements/", views.StockMovementListView.as_view(), name="stock-movements"),
    path("suppliers/", views.SupplierListView.as_view(), name="supplier-list"),
    path("batches/", views.BatchListView.as_view(), name="batch-list"),
    path("orders/", views.PurchaseOrderListView.as_view(), name="po-list"),
    path("orders/<uuid:pk>/receive/", views.POReceiveView.as_view(), name="po-receive"),
    path("dashboard/", views.InventoryDashboardView.as_view(), name="dashboard"),
]
