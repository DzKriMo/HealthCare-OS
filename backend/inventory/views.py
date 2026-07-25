"""
Inventory views — items, stock, suppliers, purchase orders.
"""
from django.utils import timezone
from django.db import models as db_models
from django.db.models import Q
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import InventoryItem, StockMovement, Supplier, PurchaseOrder, Batch
from . import serializers


@extend_schema(tags=["inventory"])
class ItemListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.InventoryItemCreateSerializer
        return serializers.InventoryItemSerializer

    def get_queryset(self):
        qs = InventoryItem.objects.for_tenant(self.request.tenant).filter(is_active=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        low_stock = self.request.query_params.get("low_stock")
        if low_stock == "true":
            qs = qs.filter(quantity_on_hand__lte=db_models.F("reorder_point"), reorder_point__gt=0)
        search = self.request.query_params.get("q")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search) | Q(barcode__icontains=search))
        return qs

    def get_required_permission(self):
        return "inventory.create_po" if self.request.method == "POST" else "inventory.read"


@extend_schema(tags=["inventory"])
class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.InventoryItemSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_queryset(self):
        return InventoryItem.objects.for_tenant(self.request.tenant)

    def get_required_permission(self):
        if self.request.method == "GET":
            return "inventory.read"
        return "inventory.adjust_stock"

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


@extend_schema(tags=["inventory"])
class StockAdjustmentView(views.APIView):
    """Adjust stock: inventory count, write-off waste, returns."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "inventory.adjust_stock"

    def post(self, request):
        s = serializers.StockAdjustmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        try:
            item = InventoryItem.objects.for_tenant(request.tenant).get(id=d["item_id"])
        except InventoryItem.DoesNotExist:
            return Response({"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        batch = None
        if d.get("batch_id"):
            try:
                batch = Batch.objects.for_tenant(request.tenant).get(id=d["batch_id"])
            except Batch.DoesNotExist:
                pass

        quantity = d["quantity"]
        if d["movement_type"] in ("waste", "out"):
            quantity = -abs(quantity)

        movement = StockMovement.objects.create(
            tenant=request.tenant, item=item, batch=batch,
            movement_type=d["movement_type"], quantity=quantity,
            reason=d.get("reason", ""), performed_by=request.user,
        )

        return Response(serializers.StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["inventory"])
class StockMovementListView(generics.ListAPIView):
    serializer_class = serializers.StockMovementSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "inventory.read"

    def get_queryset(self):
        qs = StockMovement.objects.for_tenant(self.request.tenant).select_related("item", "performed_by")
        item_id = self.request.query_params.get("item")
        if item_id:
            qs = qs.filter(item_id=item_id)
        return qs


@extend_schema(tags=["inventory"])
class SupplierListView(generics.ListCreateAPIView):
    serializer_class = serializers.SupplierSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_queryset(self):
        return Supplier.objects.for_tenant(self.request.tenant).filter(is_active=True)

    def get_required_permission(self):
        return "inventory.manage_suppliers" if self.request.method == "POST" else "inventory.read"

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["inventory"])
class BatchListView(generics.ListCreateAPIView):
    serializer_class = serializers.BatchSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_queryset(self):
        qs = Batch.objects.for_tenant(self.request.tenant).filter(is_active=True).select_related("item")
        item_id = self.request.query_params.get("item")
        if item_id:
            qs = qs.filter(item_id=item_id)
        expiring = self.request.query_params.get("expiring_soon")
        if expiring == "true":
            cutoff = timezone.now().date() + timezone.timedelta(days=90)
            qs = qs.filter(expiration_date__lte=cutoff, expiration_date__gte=timezone.now().date())
        return qs

    def get_required_permission(self):
        return "inventory.manage_batches" if self.request.method == "POST" else "inventory.read"


@extend_schema(tags=["inventory"])
class PurchaseOrderListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.PurchaseOrderCreateSerializer
        return serializers.PurchaseOrderSerializer

    def get_queryset(self):
        return PurchaseOrder.objects.for_tenant(self.request.tenant).select_related("supplier")

    def get_required_permission(self):
        return "inventory.create_po" if self.request.method == "POST" else "inventory.read"


@extend_schema(tags=["inventory"])
class POReceiveView(views.APIView):
    """Receive items against a purchase order."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "inventory.receive_po"

    def post(self, request, pk):
        try:
            po = PurchaseOrder.objects.for_tenant(request.tenant).get(pk=pk)
        except PurchaseOrder.DoesNotExist:
            return Response({"error": "PO not found."}, status=status.HTTP_404_NOT_FOUND)

        if po.status == PurchaseOrder.Status.RECEIVED:
            return Response({"error": "PO already fully received."}, status=status.HTTP_400_BAD_REQUEST)

        r = serializers.POReceiveSerializer(data=request.data)
        r.is_valid(raise_exception=True)
        po.receive(request.user, r.validated_data["item_receipts"])

        return Response(serializers.PurchaseOrderSerializer(po).data)


@extend_schema(tags=["inventory"], summary="Low stock and expiring items dashboard")
class InventoryDashboardView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "inventory.read"

    def get(self, request):
        tenant = request.tenant

        low_stock = InventoryItem.objects.for_tenant(tenant).filter(
            is_active=True, quantity_on_hand__lte=db_models.F("reorder_point"), reorder_point__gt=0,
        ).count()

        cutoff = timezone.now().date() + timezone.timedelta(days=90)
        expiring = Batch.objects.for_tenant(tenant).filter(
            is_active=True, expiration_date__lte=cutoff, expiration_date__gte=timezone.now().date(),
        ).count()

        pending_pos = PurchaseOrder.objects.for_tenant(tenant).filter(
            status__in=["draft", "sent", "partially_received"],
        ).count()

        total_value = InventoryItem.objects.for_tenant(tenant).filter(is_active=True).aggregate(
            v=db_models.Sum(db_models.F("quantity_on_hand") * db_models.F("unit_cost"))
        )["v"] or 0

        return Response({
            "low_stock_count": low_stock,
            "expiring_batches": expiring,
            "pending_pos": pending_pos,
            "total_stock_value": str(total_value),
        })
