import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


class AISettings(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="ai_settings", primary_key=True)
    provider = models.CharField(
        max_length=50, default="openai",
        choices=[("openai", "OpenAI"), ("local", "Local/Offline"), ("custom", "Custom Endpoint")],
    )
    api_key = models.CharField(max_length=500, blank=True, help_text="Encrypted API key")
    api_endpoint = models.URLField(max_length=500, blank=True, help_text="Custom endpoint URL")
    model = models.CharField(max_length=100, default="gpt-4o-mini")
    temperature = models.FloatField(default=0.3)
    max_tokens = models.IntegerField(default=1024)
    enabled_features = models.JSONField(
        default=dict,
        help_text="Feature flags: {icd10_suggestion: true, soap_generation: true, drug_interaction: true, symptom_analysis: true}",
    )
    require_human_review = models.BooleanField(
        default=True,
        help_text="Require clinician approval before using AI suggestions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_diagnostics_settings"

    def __str__(self):
        return f"AI Settings for {self.tenant}"


class AISuggestion(models.Model):
    class SuggestionType(models.TextChoices):
        ICD10_SUGGESTION = "icd10", "ICD-10 Code Suggestion"
        SOAP_DRAFT = "soap", "SOAP Note Draft"
        DRUG_INTERACTION = "drug_interaction", "Drug Interaction Check"
        SYMPTOM_ANALYSIS = "symptom", "Symptom Analysis"
        IMAGE_ANALYSIS = "image", "Image Analysis"
        TREATMENT_PLAN = "treatment", "Treatment Plan Suggestion"
        CPT_CODING = "cpt", "CPT Code Suggestion"
        PRESCRIPTION_DRAFT = "prescription", "Prescription Draft"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="ai_suggestions")
    suggestion_type = models.CharField(max_length=30, choices=SuggestionType.choices, db_index=True)
    patient = models.ForeignKey("patients.Patient", on_delete=models.SET_NULL, null=True, blank=True)
    encounter = models.ForeignKey("clinical.Encounter", on_delete=models.SET_NULL, null=True, blank=True)
    input_data = models.JSONField(help_text="Input context provided to the AI")
    output_data = models.JSONField(help_text="AI generated output")
    confidence = models.FloatField(null=True, blank=True, help_text="Confidence score 0-1")
    accepted = models.BooleanField(null=True, help_text="True=accepted, False=rejected, Null=pending")
    accepted_by = models.ForeignKey(
        "identity.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="accepted_suggestions",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True, help_text="AI response time")
    model_used = models.CharField(max_length=100, blank=True)
    is_fallback = models.BooleanField(
        default=False,
        help_text="True if offline/local fallback was used instead of cloud AI",
    )
    error = models.TextField(blank=True, help_text="Error message if AI call failed")
    created_by = models.ForeignKey("identity.User", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ai_diagnostics_suggestion"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "suggestion_type"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "accepted"]),
        ]

    def __str__(self):
        return f"{self.get_suggestion_type_display()} ({self.confidence})"


class AIAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="ai_audit_logs")
    user = models.ForeignKey("identity.User", on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=[
        ("suggestion_generated", "Suggestion Generated"),
        ("suggestion_accepted", "Suggestion Accepted"),
        ("suggestion_rejected", "Suggestion Rejected"),
        ("settings_updated", "Settings Updated"),
        ("error", "Error"),
    ])
    suggestion = models.ForeignKey(AISuggestion, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "ai_diagnostics_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "action"]),
            models.Index(fields=["tenant", "created_at"]),
        ]
