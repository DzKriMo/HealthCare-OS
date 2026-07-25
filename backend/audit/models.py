"""
Immutable audit event model — Sprint 6.

Every sensitive action produces an AuditEvent that is append-only.
No updates, no deletes. This is the compliance backbone of the platform.
"""
import uuid
from django.db import models
from tenancy.models import Tenant


class AuditEvent(models.Model):
    """
    Immutable audit record.

    Captures: who, what, when, where, before/after values.
    Once created, this record CANNOT be modified — not even by admins.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="audit_events",
        null=True, blank=True,
    )

    # Actor
    actor = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, blank=True,
        related_name="audit_events",
    )
    actor_display = models.CharField(
        max_length=200, blank=True,
        help_text="Snapshot of actor name at time of action.",
    )

    # Session context
    session_id = models.CharField(max_length=100, blank=True, default="")
    correlation_id = models.CharField(
        max_length=100, db_index=True, blank=True, default="",
        help_text="Links related audit events.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Target
    entity_type = models.CharField(
        max_length=100, db_index=True,
        help_text="Model or resource type, e.g. 'Patient', 'Invoice'.",
    )
    entity_id = models.CharField(
        max_length=100, blank=True, db_index=True,
        help_text="UUID or identifier of the affected entity.",
    )
    entity_display = models.CharField(
        max_length=300, blank=True,
        help_text="Human-readable label for the entity.",
    )

    # Action
    action = models.CharField(
        max_length=100, db_index=True,
        help_text="create, update, delete, read, login, logout, export, etc.",
    )

    # Change data (JSON)
    before_value = models.JSONField(null=True, blank=True)
    after_value = models.JSONField(null=True, blank=True)

    # Metadata
    is_sensitive = models.BooleanField(
        default=False,
        help_text="Marks events on sensitive data for extra retention.",
    )
    extra = models.JSONField(default=dict, blank=True)

    # Timestamp (immutable)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "entity_type", "entity_id"]),
            models.Index(fields=["tenant", "actor"]),
            models.Index(fields=["tenant", "action"]),
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.actor_display} {self.action} {self.entity_type}#{self.entity_id}"

    def delete(self, *args, **kwargs):
        """Prevent deletion of audit events."""
        raise RuntimeError("AuditEvent records are immutable and cannot be deleted.")
