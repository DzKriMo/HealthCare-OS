import logging
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("healthcare_os.billing.gateway")

try:
    import stripe
except ImportError:
    stripe = None


class PaymentGatewayService:
    def __init__(self, tenant):
        self.tenant = tenant
        self.config = self._load_config()

    def _load_config(self):
        from integrations.models import PaymentProviderConfig
        config = PaymentProviderConfig.objects.filter(
            tenant=self.tenant, is_enabled=True,
        ).first()
        return config

    def _get_stripe_key(self):
        if self.config and self.config.provider == "stripe" and self.config.api_secret:
            return self.config.api_secret
        return getattr(settings, "STRIPE_SECRET_KEY", "")

    def _get_stripe_public_key(self):
        if self.config and self.config.provider == "stripe" and self.config.public_key:
            return self.config.public_key
        return getattr(settings, "STRIPE_PUBLISHABLE_KEY", "")

    def create_checkout_session(self, invoice, success_url: str, cancel_url: str, gateway: str = "stripe") -> dict:
        if gateway == "paypal":
            return self._create_paypal_order(invoice, success_url, cancel_url)
        return self._create_stripe_session(invoice, success_url, cancel_url)

    def _create_stripe_session(self, invoice, success_url: str, cancel_url: str) -> dict:
        if not stripe:
            return {"error": "Stripe SDK not installed"}
        stripe.api_key = self._get_stripe_key()
        if not stripe.api_key:
            return self._log_fallback("stripe", invoice)

        try:
            amount_cents = int(invoice.balance_due * Decimal("100"))
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Invoice {invoice.invoice_number}",
                            "description": f"Payment for invoice {invoice.invoice_number}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                metadata={"invoice_id": str(invoice.id), "tenant_id": str(self.tenant.id)},
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
            )
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "gateway": "stripe",
                "public_key": self._get_stripe_public_key(),
            }
        except Exception as e:
            logger.error(f"Stripe session creation failed: {e}")
            return {"error": str(e)}

    def _create_paypal_order(self, invoice, success_url: str, cancel_url: str) -> dict:
        return {
            "session_id": "",
            "checkout_url": "",
            "gateway": "paypal",
            "public_key": self.config.public_key if self.config else "",
            "note": "PayPal integration requires additional setup",
        }

    def handle_webhook(self, payload: bytes, sig_header: str, gateway: str = "stripe") -> dict:
        if gateway == "stripe":
            return self._handle_stripe_webhook(payload, sig_header)
        return {"status": "unsupported_gateway"}

    def _handle_stripe_webhook(self, payload: bytes, sig_header: str) -> dict:
        if not stripe:
            return {"error": "Stripe SDK not installed"}
        stripe.api_key = self._get_stripe_key()
        webhook_secret = self.config.webhook_secret if self.config else ""
        if not webhook_secret:
            webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error(f"Stripe webhook verification failed: {e}")
            return {"error": str(e)}

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            self._process_completed_checkout(session)

        return {"status": "processed", "event_type": event["type"]}

    def _process_completed_checkout(self, session):
        from .models import Invoice, Payment
        invoice_id = session.get("metadata", {}).get("invoice_id")
        if not invoice_id:
            return
        try:
            invoice = Invoice.objects.for_tenant(self.tenant).get(id=invoice_id)
            amount = Decimal(str(session.get("amount_total", 0))) / Decimal("100")
            Payment.objects.create(
                tenant=self.tenant,
                patient=invoice.patient,
                amount=amount,
                method=Payment.Method.ONLINE,
                gateway=Payment.Gateway.STRIPE,
                gateway_payment_id=session.get("payment_intent", session.get("id", "")),
                reference=f"stripe_{session.get('id', '')}",
                allocations=[{"invoice_id": invoice_id, "amount": str(amount)}],
                payment_date=timezone.now(),
            )
        except Invoice.DoesNotExist:
            logger.error(f"Invoice {invoice_id} not found for Stripe webhook")

    def _log_fallback(self, gateway_name: str, invoice) -> dict:
        logger.info(f"[{gateway_name.upper()} FALLBACK] Invoice {invoice.invoice_number}")
        return {"error": f"{gateway_name} is not configured", "fallback": True}


def get_public_key(tenant) -> str:
    from integrations.models import PaymentProviderConfig
    config = PaymentProviderConfig.objects.filter(tenant=tenant, is_enabled=True).first()
    if config:
        return config.public_key
    return getattr(settings, "STRIPE_PUBLISHABLE_KEY", "")
