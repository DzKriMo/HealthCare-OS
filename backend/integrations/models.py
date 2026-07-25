"""
Integration models — webhooks, plugins, external connectors.

Webhook system: endpoints register for events. When an event fires,
the webhook dispatcher delivers a signed payload and retries on failure.
"""
import uuid
import json
import hmac
import hashlib
import logging
import requests
from django.db import models
from django.utils import timezone

from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager

logger = logging.getLogger("healthcare_os.integrations")


class WebhookEndpoint(models.Model):
    """
    A registered webhook endpoint that receives event notifications.

    Events are signed with HMAC-SHA256 for verification.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="webhooks")
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=200, help_text="HMAC signing secret.")

    # Which events to listen for
    events = models.JSONField(
        default=list,
        help_text='List of event types: ["appointment.scheduled", "invoice.paid"].',
    )

    is_active = models.BooleanField(default=True)
    retry_count = models.IntegerField(default=3, help_text="Max retry attempts on failure.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integrations_webhook"

    def __str__(self):
        return f"Webhook: {self.name} → {self.url}"

    def deliver(self, event_type: str, payload: dict) -> "WebhookDelivery":
        """Deliver this event to the webhook endpoint."""
        delivery = WebhookDelivery.objects.create(
            webhook=self,
            event_type=event_type,
            payload=payload,
        )

        success = self._send(delivery)
        delivery.status = "delivered" if success else "failed"
        delivery.attempts = 1

        # Retry on failure
        if not success:
            for attempt in range(2, self.retry_count + 1):
                success = self._send(delivery)
                delivery.attempts = attempt
                if success:
                    delivery.status = "delivered"
                    break

        delivery.completed_at = timezone.now()
        delivery.save(update_fields=["status", "attempts", "completed_at", "response_body", "response_status"])
        return delivery

    def _send(self, delivery: "WebhookDelivery") -> bool:
        """Send the webhook with HMAC signature."""
        try:
            body = json.dumps(delivery.payload)
            signature = hmac.new(
                self.secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()

            response = requests.post(
                self.url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Event-Type": delivery.event_type,
                    "X-Delivery-ID": str(delivery.id),
                },
                timeout=10,
            )
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]
            return 200 <= response.status_code < 300
        except Exception as e:
            delivery.response_body = str(e)[:1000]
            return False


class WebhookDelivery(models.Model):
    """Delivery log for a webhook event."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries")
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, default="pending",
        choices=[("pending", "Pending"), ("delivered", "Delivered"), ("failed", "Failed")],
    )
    attempts = models.IntegerField(default=0)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "integrations_webhook_delivery"
        ordering = ["-created_at"]


# ═══════════════════════════════════════════════════════════════
# Payment Provider Configs — Sprint B10
# ═══════════════════════════════════════════════════════════════

class PaymentProviderConfig(models.Model):
    """Per-tenant payment gateway configuration."""

    class Provider(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"
        CUSTOM = "custom", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="payment_configs")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    is_enabled = models.BooleanField(default=False)
    is_test_mode = models.BooleanField(default=True)
    api_key = models.CharField(max_length=500, blank=True, help_text="Encrypted at rest.")
    api_secret = models.CharField(max_length=500, blank=True, help_text="Encrypted at rest.")
    webhook_secret = models.CharField(max_length=500, blank=True)
    public_key = models.CharField(max_length=500, blank=True)
    supported_currencies = models.JSONField(default=list, help_text='["USD","EUR","GBP"]')
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integrations_payment_config"
        unique_together = ["tenant", "provider"]

    def __str__(self): return f"{self.provider} — {self.tenant.name} ({'enabled' if self.is_enabled else 'disabled'})"


class CalendarProviderConfig(models.Model):
    """Per-tenant calendar sync configuration."""

    class Provider(models.TextChoices):
        GOOGLE = "google", "Google Calendar"
        OUTLOOK = "outlook", "Microsoft Outlook / 365"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="calendar_configs")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    is_enabled = models.BooleanField(default=False)
    sync_direction = models.CharField(max_length=20, choices=[("two_way","Two-Way"),("export","Export Only"),("import","Import Only")], default="two_way")
    client_id = models.CharField(max_length=500, blank=True)
    client_secret = models.CharField(max_length=500, blank=True)
    refresh_token = models.CharField(max_length=500, blank=True)
    calendar_id = models.CharField(max_length=200, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integrations_calendar_config"
        unique_together = ["tenant", "provider"]

    def __str__(self): return f"{self.provider} — {self.tenant.name}"


class CommunicationProviderConfig(models.Model):
    """Per-tenant communication provider settings."""

    class Channel(models.TextChoices):
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email Provider"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="comm_configs")
    channel = models.CharField(max_length=20, choices=Channel.choices)
    provider_name = models.CharField(max_length=100, help_text="twilio, vonage, sendgrid, mailgun, etc.")
    is_enabled = models.BooleanField(default=False)
    api_key = models.CharField(max_length=500, blank=True)
    api_secret = models.CharField(max_length=500, blank=True)
    from_number = models.CharField(max_length=30, blank=True, help_text="Sender phone number.")
    from_email = models.EmailField(blank=True)
    webhook_secret = models.CharField(max_length=500, blank=True)
    settings = models.JSONField(default=dict)
    daily_limit = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integrations_comm_config"
        unique_together = ["tenant", "channel", "provider_name"]

    def __str__(self): return f"{self.channel} ({self.provider_name}) — {self.tenant.name}"


# Insurance EDI — Sprint B11

class InsuranceClearinghouseConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="clearinghouse_configs")
    name = models.CharField(max_length=200)
    is_enabled = models.BooleanField(default=False); is_test_mode = models.BooleanField(default=True)
    ftp_host = models.CharField(max_length=300, blank=True); ftp_username = models.CharField(max_length=200, blank=True)
    ftp_password = models.CharField(max_length=200, blank=True); api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=500, blank=True); sender_id = models.CharField(max_length=100, blank=True)
    receiver_id = models.CharField(max_length=100, blank=True)
    supported_transactions = models.JSONField(default=list)
    last_submission_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = "integrations_clearinghouse"; unique_together = ["tenant","name"]
    def __str__(self): return f"Clearinghouse: {self.name} — {self.tenant.name}"


class EDIClaimSubmission(models.Model):
    class Status(models.TextChoices): DRAFT="draft","Draft"; SUBMITTED="submitted","Submitted"; ACKNOWLEDGED="acknowledged","Acknowledged"; PENDING="pending","Pending"; PAID="paid","Paid"; DENIED="denied","Denied"; REJECTED="rejected","Rejected"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="edi_claims")
    clearinghouse = models.ForeignKey(InsuranceClearinghouseConfig, on_delete=models.PROTECT, null=True)
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT, null=True, related_name="edi_submissions")
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, null=True)
    claim_number = models.CharField(max_length=100, unique=True); status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    transaction_type = models.CharField(max_length=10, choices=[("837P","Professional"),("837I","Institutional"),("837D","Dental")], default="837P")
    edi_payload = models.TextField(blank=True); response_edi = models.TextField(blank=True)
    submitted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    denial_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True); responded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True); created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta: db_table = "integrations_edi_claim"; ordering = ["-created_at"]; indexes = [models.Index(fields=["tenant"]),models.Index(fields=["status"])]
    def __str__(self): return f"EDI Claim {self.claim_number} — {self.status}"


class EligibilityCheck(models.Model):
    class Status(models.TextChoices): PENDING="pending","Pending"; ACTIVE="active","Coverage Active"; INACTIVE="inactive","Coverage Inactive"; ERROR="error","Error"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="eligibility_checks")
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, null=True)
    insurance_policy = models.ForeignKey("patients.InsurancePolicy", on_delete=models.PROTECT, null=True)
    check_date = models.DateTimeField(default=timezone.now); status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    response_summary = models.JSONField(default=dict); raw_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta: db_table = "integrations_eligibility"; ordering = ["-check_date"]
    def __str__(self): return f"Eligibility {self.patient} — {self.status}"


# Accounting Integration

class AccountingProviderConfig(models.Model):
    class Provider(models.TextChoices): QUICKBOOKS="quickbooks","QuickBooks Online"; XERO="xero","Xero"; CUSTOM="custom","Custom"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="accounting_configs")
    provider = models.CharField(max_length=20, choices=Provider.choices); is_enabled = models.BooleanField(default=False)
    client_id = models.CharField(max_length=500, blank=True); client_secret = models.CharField(max_length=500, blank=True)
    refresh_token = models.CharField(max_length=500, blank=True); realm_id = models.CharField(max_length=200, blank=True)
    chart_of_accounts_map = models.JSONField(default=dict)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = "integrations_accounting"; unique_together = ["tenant","provider"]
    def __str__(self): return f"{self.provider} — {self.tenant.name}"


# Government API Connectors

class GovernmentConnectorConfig(models.Model):
    class ConnectorType(models.TextChoices): PDMP="pdmp","Prescription Drug Monitoring"; NOTIFIABLE="notifiable","Notifiable Disease Reporting"; IMMUNIZATION="immunization","Immunization Registry"; CUSTOM="custom","Custom"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="gov_connectors")
    connector_type = models.CharField(max_length=20, choices=ConnectorType.choices); is_enabled = models.BooleanField(default=False)
    api_endpoint = models.URLField(blank=True); api_key = models.CharField(max_length=500, blank=True)
    facility_id = models.CharField(max_length=200, blank=True); settings = models.JSONField(default=dict)
    last_submission_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = "integrations_gov"; unique_together = ["tenant","connector_type"]
    def __str__(self): return f"{self.connector_type} — {self.tenant.name}"


# Plugin Marketplace — Sprint B12

class Plugin(models.Model):
    """A plugin available in the marketplace."""

    class Category(models.TextChoices):
        COMMUNICATION = "communication", "Communication"
        PAYMENT = "payment", "Payment"
        CALENDAR = "calendar", "Calendar"
        INSURANCE = "insurance", "Insurance"
        ACCOUNTING = "accounting", "Accounting"
        CLINICAL = "clinical", "Clinical"
        REPORTING = "reporting", "Reporting"
        AI = "ai", "AI & Analytics"
        OTHER = "other", "Other"

    class PricingType(models.TextChoices):
        FREE = "free", "Free"
        PAID = "paid", "One-Time Purchase"
        SUBSCRIPTION = "subscription", "Subscription"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    version = models.CharField(max_length=20)
    author = models.CharField(max_length=300)
    author_email = models.EmailField(blank=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    icon_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    pricing_type = models.CharField(max_length=20, choices=PricingType.choices, default=PricingType.FREE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subscription_interval = models.CharField(max_length=20, choices=[("monthly","Monthly"),("yearly","Yearly")], blank=True)

    # Capabilities: what this plugin registers
    capabilities = models.JSONField(default=dict, help_text="Webhooks, settings UI, menu items, billing hooks, notification channels, event listeners, background jobs.")

    # Certification
    is_certified = models.BooleanField(default=False)
    certified_at = models.DateTimeField(null=True, blank=True)
    certified_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, blank=True)
    certification_notes = models.TextField(blank=True)

    # Stats
    install_count = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)

    class Meta: db_table = "marketplace_plugin"; ordering = ["-install_count"]

    def __str__(self): return f"{self.name} v{self.version} by {self.author}"


class PluginInstallation(models.Model):
    """A plugin installed by a specific tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="plugin_installations")
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name="installations")

    is_enabled = models.BooleanField(default=True)
    config = models.JSONField(default=dict, help_text="Plugin-specific configuration.")
    installed_version = models.CharField(max_length=20)
    installed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: db_table = "marketplace_installation"; unique_together = ["tenant","plugin"]
    def __str__(self): return f"{self.plugin.name} @ {self.tenant.name}"


class PluginReview(models.Model):
    """User review and rating for a plugin."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name="reviews")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="plugin_reviews")
    reviewer = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True)

    rating = models.IntegerField(choices=[(1,"1"),(2,"2"),(3,"3"),(4,"4"),(5,"5")])
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: db_table = "marketplace_review"; unique_together = ["plugin","tenant","reviewer"]; ordering = ["-created_at"]
    def __str__(self): return f"Review: {self.plugin.name} — {self.rating}/5"


# HL7 v2 Messages — Sprint B13

class HL7Message(models.Model):
    """Inbound/outbound HL7 v2 message."""

    class MessageType(models.TextChoices):
        ADT = "ADT", "Admit/Discharge/Transfer"
        ORM = "ORM", "Order Entry"
        ORU = "ORU", "Observation Result"
        SIU = "SIU", "Schedule Information Unsolicited"
        MDM = "MDM", "Medical Document Management"

    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="hl7_messages")
    message_type = models.CharField(max_length=10, choices=MessageType.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    trigger_event = models.CharField(max_length=10, blank=True, help_text="e.g., A01, A03, O01, R01")
    sending_facility = models.CharField(max_length=200, blank=True)
    receiving_facility = models.CharField(max_length=200, blank=True)
    message_content = models.TextField(blank=True, help_text="Raw HL7 pipe-delimited message.")
    parsed_data = models.JSONField(default=dict, help_text="Parsed HL7 segments as JSON.")
    status = models.CharField(max_length=20, choices=[("received","Received"),("processed","Processed"),("error","Error")], default="received")
    error_message = models.TextField(blank=True)
    patient = models.ForeignKey("patients.Patient", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta: db_table = "integrations_hl7"; ordering = ["-created_at"]
    def __str__(self): return f"HL7 {self.message_type} {self.direction} — {self.created_at}"
