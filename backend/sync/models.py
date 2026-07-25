"""
Offline sync engine — Sprint 9.

Dual-database model: PostgreSQL (cloud) + SQLite (desktop local).

The sync engine:
    1. Queues local mutations on the desktop (SQLite sync_queue table).
    2. On reconnect, pushes queued operations to the cloud.
    3. Cloud validates each operation, checks for conflicts, accepts or rejects.
    4. Desktop pulls changes from cloud since last sync timestamp.
    5. Conflicts are resolved per entity type with configurable strategies.
"""
import uuid
import datetime
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


class DeviceRegistration(models.Model):
    """
    Registered desktop/mobile device for a tenant.

    Each device has a unique ID used for sync tracking.
    Only registered devices can push sync operations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=200, help_text="e.g. 'Front Desk PC'.")
    device_id = models.CharField(max_length=100, unique=True, help_text="Hardware/install UUID.")
    platform = models.CharField(max_length=20, default="desktop", choices=[("desktop","Desktop"),("mobile","Mobile")])

    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_cursor = models.CharField(
        max_length=100, blank=True,
        help_text="Last synced event timestamp/cursor for pull.",
    )

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sync_device"

    def __str__(self):
        return f"{self.device_name} ({self.tenant.slug})"


class SyncOperation(models.Model):
    """
    A single offline mutation queued for cloud replay.

    Each operation is idempotent — replaying the same operation
    multiple times must produce the same result.
    """

    class OperationType(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SYNCING = "syncing", "Syncing"
        SYNCED = "synced", "Synced"
        CONFLICT = "conflict", "Conflict"
        FAILED = "failed", "Failed"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="sync_operations")

    # Source
    device = models.ForeignKey(DeviceRegistration, on_delete=models.CASCADE, related_name="operations")
    user = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, blank=True,
        related_name="sync_operations",
    )

    # Target entity
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=100, db_index=True)
    operation_type = models.CharField(max_length=10, choices=OperationType.choices)

    # Payload
    payload = models.JSONField(default=dict, help_text="Full or diff payload.")
    base_version = models.IntegerField(
        default=0,
        help_text="Version the client thinks the record is at. Used for conflict detection.",
    )

    # Ordering
    client_timestamp = models.DateTimeField(help_text="When this operation was created on the client.")
    sequence_number = models.BigIntegerField(help_text="Monotonic sequence from the client device.")

    # Dependencies
    dependencies = models.JSONField(
        default=list,
        help_text="List of operation IDs that must be processed first.",
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=5)
    last_error = models.TextField(blank=True)

    # Idempotency
    idempotency_key = models.CharField(
        max_length=100, unique=True, db_index=True,
        help_text="Client-generated UUID. Replaying this key is safe.",
    )

    # Server-side
    server_timestamp = models.DateTimeField(null=True, blank=True)
    server_version = models.IntegerField(null=True, blank=True)
    conflict_info = models.JSONField(
        null=True, blank=True,
        help_text="Conflict details if status=conflict.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "sync_operation"
        ordering = ["sequence_number"]
        indexes = [
            models.Index(fields=["tenant", "device"]),
            models.Index(fields=["tenant", "entity_type", "entity_id"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["idempotency_key"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device", "sequence_number"],
                name="unique_device_sequence",
            ),
        ]

    def __str__(self):
        return f"{self.operation_type} {self.entity_type}#{self.entity_id} [{self.status}]"


class SyncState(models.Model):
    """
    Per-device sync state — tracks what has been synced and when.
    """

    device = models.OneToOneField(DeviceRegistration, on_delete=models.CASCADE, related_name="sync_state")
    last_pull_cursor = models.CharField(max_length=100, blank=True)
    last_push_sequence = models.BigIntegerField(default=0)
    pending_count = models.IntegerField(default=0)
    conflict_count = models.IntegerField(default=0)

    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_success = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sync_state"


class ConflictResolutionRule(models.Model):
    """
    Per-entity-type conflict resolution strategy.

    Strategies:
        - last_write_wins: Newer operation wins (safe for non-clinical metadata).
        - client_wins: Client operation always accepted.
        - server_wins: Server state preserved, client operation rejected.
        - merge: Three-way merge attempted (safe fields auto-merged).
        - manual: Escalate for human review (clinical data).
    """

    class Strategy(models.TextChoices):
        LAST_WRITE_WINS = "last_write_wins", "Last Write Wins"
        CLIENT_WINS = "client_wins", "Client Wins"
        SERVER_WINS = "server_wins", "Server Wins"
        MERGE = "merge", "Auto-Merge"
        MANUAL = "manual", "Manual Review"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="conflict_rules")
    entity_type = models.CharField(max_length=100)
    strategy = models.CharField(max_length=20, choices=Strategy.choices, default=Strategy.MANUAL)
    merge_safe_fields = models.JSONField(
        default=list,
        help_text="Fields safe to auto-merge. Only used with MERGE strategy.",
    )

    class Meta:
        db_table = "sync_conflict_rule"
        unique_together = ["tenant", "entity_type"]

    def __str__(self):
        return f"{self.entity_type}: {self.strategy}"
