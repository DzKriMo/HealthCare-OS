"""
Sync API views — push, pull, device registration, conflict rules.
"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import DeviceRegistration, SyncOperation, SyncState, ConflictResolutionRule
from .engine import SyncEngine
from . import serializers


@extend_schema(tags=["sync"])
class DeviceRegisterView(generics.GenericAPIView):
    """Register a desktop/mobile device for sync."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "sync.access"

    def post(self, request):
        result = SyncEngine.register_device(
            tenant=request.tenant,
            device_name=request.data.get("device_name", "Unknown"),
            device_id=request.data.get("device_id", ""),
            platform=request.data.get("platform", "desktop"),
        )
        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


@extend_schema(tags=["sync"], summary="Push offline operations to cloud")
class SyncPushView(generics.GenericAPIView):
    """
    Push queued offline operations from a device to the server.

    POST /api/sync/push/
    Body: { "device_id": "...", "operations": [...] }
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "sync.access"

    def post(self, request):
        req_serializer = serializers.PushRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)

        result = SyncEngine.push(
            tenant=request.tenant,
            device_id=req_serializer.validated_data["device_id"],
            operations=req_serializer.validated_data["operations"],
        )

        return Response(result)


@extend_schema(tags=["sync"], summary="Pull changes from cloud")
class SyncPullView(generics.GenericAPIView):
    """
    Pull changes since the device's last sync cursor.

    POST /api/sync/pull/
    Body: { "device_id": "...", "since_cursor": "..." }
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "sync.access"

    def post(self, request):
        req_serializer = serializers.PullRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)

        result = SyncEngine.pull(
            tenant=request.tenant,
            device_id=req_serializer.validated_data["device_id"],
            since_cursor=req_serializer.validated_data.get("since_cursor", ""),
        )

        return Response(result)


@extend_schema(tags=["sync"])
class SyncStatusView(generics.GenericAPIView):
    """Get sync status for a device."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "sync.access"

    def get(self, request):
        device_id = request.query_params.get("device_id")
        if not device_id:
            return Response({"error": "device_id required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = DeviceRegistration.objects.get(tenant=request.tenant, device_id=device_id)
            state = SyncState.objects.get(device=device)
        except DeviceRegistration.DoesNotExist:
            return Response({"error": "Device not found."}, status=status.HTTP_404_NOT_FOUND)
        except SyncState.DoesNotExist:
            return Response({"pending": 0, "conflicts": 0, "last_sync": None})

        pending = SyncOperation.objects.for_tenant(request.tenant).filter(
            device=device, status="pending",
        ).count()

        conflicts = SyncOperation.objects.for_tenant(request.tenant).filter(
            device=device, status="conflict",
        ).count()

        return Response({
            "device_name": device.device_name,
            "is_active": device.is_active,
            "last_sync": state.last_sync_at,
            "pending_count": pending,
            "conflict_count": conflicts,
            "last_cursor": device.sync_cursor,
        })


@extend_schema(tags=["sync"])
class ConflictRulesView(generics.ListCreateAPIView):
    """Get or set conflict resolution rules per entity type."""
    serializer_class = serializers.ConflictRuleSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "sync.access"

    def get_queryset(self):
        return ConflictResolutionRule.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
