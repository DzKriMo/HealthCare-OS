"""FHIR configuration models."""
import uuid
from django.db import models
from tenancy.models import Tenant


class SMARTonFHIRConfig(models.Model):
    """SMART on FHIR configuration for third-party app access."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="smart_configs")
    is_enabled = models.BooleanField(default=False)
    issuer_url = models.URLField(blank=True, help_text="FHIR base URL, e.g. https://app.healthcare-os.com/fhir")
    authorization_endpoint = models.URLField(blank=True)
    token_endpoint = models.URLField(blank=True)
    supported_scopes = models.JSONField(default=list, help_text='["patient/*.read","launch/patient"]')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: db_table = "fhir_smart_config"

    def __str__(self): return f"SMART Config — {self.tenant.name}"


class FHIRAppRegistration(models.Model):
    """Registered third-party SMART app."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="fhir_apps")
    client_id = models.CharField(max_length=200, unique=True)
    client_secret = models.CharField(max_length=500, blank=True)
    app_name = models.CharField(max_length=300)
    redirect_uris = models.JSONField(default=list)
    scopes = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: db_table = "fhir_app_registration"

    def __str__(self): return f"FHIR App: {self.app_name}"
