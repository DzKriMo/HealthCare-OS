from django.contrib import admin
from .models import InventoryItem, StockMovement, Supplier, PurchaseOrder, Batch

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "quantity_on_hand", "unit", "tenant", "is_active"]
    list_filter = ["category", "is_active", "tenant"]

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["item", "movement_type", "quantity", "created_at"]
    list_filter = ["movement_type", "tenant"]

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_person", "email", "tenant", "is_active"]

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["po_number", "supplier", "status", "total_cost", "ordered_date"]

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ["lot_number", "item", "quantity", "expiration_date"]
