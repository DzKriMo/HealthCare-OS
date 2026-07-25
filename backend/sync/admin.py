from django.contrib import admin
from .models import DeviceRegistration, SyncOperation, SyncState, ConflictResolutionRule

@admin.register(DeviceRegistration)
class DeviceRegistrationAdmin(admin.ModelAdmin):
    list_display = ["device_name", "tenant", "platform", "is_active", "last_sync_at"]

@admin.register(SyncOperation)
class SyncOperationAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "entity_id", "operation_type", "status", "device", "created_at"]
    list_filter = ["status", "operation_type", "entity_type"]

@admin.register(SyncState)
class SyncStateAdmin(admin.ModelAdmin):
    list_display = ["device", "pending_count", "conflict_count", "last_sync_at"]

@admin.register(ConflictResolutionRule)
class ConflictResolutionRuleAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "strategy", "tenant"]
