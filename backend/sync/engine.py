"""
Sync engine — core logic for processing sync operations.

Handles:
    1. Push: accept queued operations from a device, validate, detect conflicts.
    2. Pull: return changes since the device's last sync cursor.
    3. Conflict resolution: per-entity-type strategies.
"""
import uuid
import logging
from django.db import models as db_models
from django.utils import timezone

from .models import (
    DeviceRegistration, SyncOperation, SyncState,
    ConflictResolutionRule,
)

logger = logging.getLogger("healthcare_os.sync")


class SyncEngine:
    """
    Stateless sync engine. Processes push and pull operations.
    """

    # Entity types that support versioning
    VERSIONED_ENTITIES = {
        "Patient": "patients_patient",
        "Appointment": "scheduling_appointment",
        "Invoice": "billing_invoice",
    }

    @classmethod
    def push(cls, tenant, device_id: str, operations: list[dict]) -> dict:
        """
        Process a batch of sync operations from a device.

        Returns: { accepted: [...], conflicted: [...], rejected: [...] }
        """
        try:
            device = DeviceRegistration.objects.get(
                tenant=tenant, device_id=device_id, is_active=True,
            )
        except DeviceRegistration.DoesNotExist:
            return {"error": "Device not registered or inactive."}

        results = {"accepted": [], "conflicted": [], "rejected": []}

        for op_data in operations:
            result = cls._process_operation(tenant, device, op_data)
            status = result.get("status", "rejected")
            if status == "accepted":
                results["accepted"].append(result)
            elif status == "conflict":
                results["conflicted"].append(result)
            else:
                results["rejected"].append(result)

        # Update device sync state
        state, _ = SyncState.objects.get_or_create(device=device)
        state.last_sync_at = timezone.now()
        state.last_sync_success = len(results["rejected"]) == 0
        state.save()

        return results

    @classmethod
    def _process_operation(cls, tenant, device, op_data: dict) -> dict:
        """Process a single operation. Returns result dict."""
        idempotency_key = op_data.get("idempotency_key", "")

        # Check for duplicate (idempotency)
        if SyncOperation.objects.filter(idempotency_key=idempotency_key).exists():
            existing = SyncOperation.objects.get(idempotency_key=idempotency_key)
            return {
                "status": "accepted",
                "idempotency_key": idempotency_key,
                "server_id": str(existing.id),
                "server_version": existing.server_version,
                "duplicate": True,
            }

        # Create sync operation record
        operation = SyncOperation.objects.create(
            tenant=tenant,
            device=device,
            user_id=op_data.get("user_id"),
            entity_type=op_data.get("entity_type", ""),
            entity_id=op_data.get("entity_id", ""),
            operation_type=op_data.get("operation_type", "update"),
            payload=op_data.get("payload", {}),
            base_version=op_data.get("base_version", 0),
            client_timestamp=op_data.get("client_timestamp", timezone.now().isoformat()),
            sequence_number=op_data.get("sequence_number", 0),
            dependencies=op_data.get("dependencies", []),
            idempotency_key=idempotency_key,
        )

        # Detect conflicts
        if cls._has_conflict(tenant, operation):
            resolution = cls._resolve_conflict(tenant, operation)

            if resolution["action"] == "reject":
                operation.status = SyncOperation.Status.CONFLICT
                operation.conflict_info = resolution
                operation.processed_at = timezone.now()
                operation.save()
                return {
                    "status": "conflict",
                    "idempotency_key": idempotency_key,
                    "server_id": str(operation.id),
                    "resolution": resolution,
                }

        # Apply the operation
        try:
            server_version = cls._apply_operation(tenant, operation)
            operation.status = SyncOperation.Status.SYNCED
            operation.server_version = server_version
            operation.server_timestamp = timezone.now()
            operation.processed_at = timezone.now()
            operation.save()

            return {
                "status": "accepted",
                "idempotency_key": idempotency_key,
                "server_id": str(operation.id),
                "server_version": server_version,
            }
        except Exception as e:
            logger.error(f"Sync operation failed: {e}")
            operation.status = SyncOperation.Status.FAILED
            operation.last_error = str(e)[:500]
            operation.retry_count += 1
            operation.save()

            return {
                "status": "rejected",
                "idempotency_key": idempotency_key,
                "error": str(e)[:500],
            }

    @classmethod
    def _has_conflict(cls, tenant, operation) -> bool:
        """Check if this operation conflicts with the current server state."""
        if operation.base_version == 0:
            return False  # New record, no conflict possible

        # For update operations: check if server version > base_version
        if operation.operation_type == "update":
            # In production: query the actual entity table for its current version
            # For now: check if any sync operation has been accepted for this entity
            # after the client's base version
            newer = SyncOperation.objects.for_tenant(tenant).filter(
                entity_type=operation.entity_type,
                entity_id=operation.entity_id,
                status=SyncOperation.Status.SYNCED,
                server_version__gt=operation.base_version,
            ).exclude(
                device=operation.device,
            ).exists()
            return newer

        return False

    @classmethod
    def _resolve_conflict(cls, tenant, operation) -> dict:
        """Resolve conflict based on configured strategy for this entity type."""
        rule = ConflictResolutionRule.objects.filter(
            tenant=tenant, entity_type=operation.entity_type,
        ).first()

        strategy = rule.strategy if rule else ConflictResolutionRule.Strategy.MANUAL

        if strategy == ConflictResolutionRule.Strategy.CLIENT_WINS:
            return {"action": "accept", "strategy": "client_wins"}
        elif strategy == ConflictResolutionRule.Strategy.SERVER_WINS:
            return {"action": "reject", "strategy": "server_wins"}
        elif strategy == ConflictResolutionRule.Strategy.LAST_WRITE_WINS:
            client_time = operation.client_timestamp
            # Find last server update time for this entity
            last_server = SyncOperation.objects.for_tenant(tenant).filter(
                entity_type=operation.entity_type,
                entity_id=operation.entity_id,
                status=SyncOperation.Status.SYNCED,
            ).order_by("-server_timestamp").first()

            if last_server and last_server.server_timestamp:
                if client_time > last_server.server_timestamp:
                    return {"action": "accept", "strategy": "last_write_wins"}
                else:
                    return {"action": "reject", "strategy": "last_write_wins"}
            return {"action": "accept", "strategy": "last_write_wins"}

        # Default: manual review
        return {
            "action": "manual_review",
            "strategy": "manual",
            "message": "Clinical data conflicts require manual resolution.",
        }

    @classmethod
    def _apply_operation(cls, tenant, operation) -> int:
        """
        Apply a sync operation to the server database.

        Returns the new server version number.
        In production: this would actually INSERT/UPDATE/DELETE the target entity.
        For now: records the operation and returns a version number.
        """
        # Increment version
        latest = SyncOperation.objects.for_tenant(tenant).filter(
            entity_type=operation.entity_type,
            entity_id=operation.entity_id,
        ).order_by("-server_version").first()

        new_version = (latest.server_version + 1) if latest and latest.server_version else 1
        return new_version

    @classmethod
    def pull(cls, tenant, device_id: str, since_cursor: str = "") -> dict:
        """
        Return all changes since the device's last sync.

        The cursor is a timestamp-based marker. Devices pass their
        last known cursor and receive everything after it.
        """
        try:
            device = DeviceRegistration.objects.get(
                tenant=tenant, device_id=device_id, is_active=True,
            )
        except DeviceRegistration.DoesNotExist:
            return {"error": "Device not registered."}

        # Get changes synced by OTHER devices since cursor
        qs = SyncOperation.objects.for_tenant(tenant).filter(
            status=SyncOperation.Status.SYNCED,
        ).exclude(device=device)

        if since_cursor:
            qs = qs.filter(server_timestamp__gt=since_cursor)

        changes = list(qs.values(
            "id", "entity_type", "entity_id", "operation_type",
            "payload", "server_version", "server_timestamp",
        ).order_by("server_timestamp")[:500])

        # Update device cursor
        if changes:
            latest = changes[-1]["server_timestamp"]
            device.sync_cursor = latest.isoformat() if hasattr(latest, "isoformat") else str(latest)
            device.last_sync_at = timezone.now()
            device.save(update_fields=["sync_cursor", "last_sync_at"])

        return {
            "changes": changes,
            "cursor": device.sync_cursor,
            "has_more": len(changes) >= 500,
        }

    @classmethod
    def register_device(cls, tenant, device_name: str, device_id: str, platform: str = "desktop") -> dict:
        """Register a new device for sync."""
        device, created = DeviceRegistration.objects.get_or_create(
            device_id=device_id,
            defaults={
                "tenant": tenant,
                "device_name": device_name,
                "platform": platform,
            },
        )
        if not created:
            device.is_active = True
            device.save(update_fields=["is_active"])

        SyncState.objects.get_or_create(device=device)

        return {
            "device_id": device.device_id,
            "registered": created,
            "sync_cursor": device.sync_cursor,
        }
