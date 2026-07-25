import logging
from django.db import models
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger("healthcare_os.bots")

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

logger = logging.getLogger("healthcare_os.bots")


class TwilioService:
    def __init__(self, tenant):
        self.tenant = tenant
        self.config = self._load_config()
        self.comm_config = self._load_comm_config()
        self.client = None
        if self.comm_config and self.comm_config.api_key:
            self.client = TwilioClient(self.comm_config.api_key, self.comm_config.api_secret)

    def _load_config(self):
        from .models import BotConfig
        try:
            return BotConfig.objects.get(tenant=self.tenant)
        except BotConfig.DoesNotExist:
            return None

    def _load_comm_config(self):
        from integrations.models import CommunicationProviderConfig
        configs = CommunicationProviderConfig.objects.filter(
            tenant=self.tenant, channel__in=["sms", "whatsapp"], is_enabled=True,
        )
        return configs.filter(provider_name__iexact="twilio").first() or configs.first()

    def send_whatsapp(self, to_phone: str, message: str, template_name: str = "") -> dict:
        if not self.client or not self.config or not self.config.whatsapp_enabled:
            return self._log_fallback("whatsapp", to_phone, message)
        try:
            from_number = f"whatsapp:{self.config.whatsapp_from_number}"
            to = f"whatsapp:{to_phone}"
            kwargs = {"body": message, "from_": from_number}
            if template_name:
                kwargs["body"] = message
            msg = self.client.messages.create(**kwargs, to=to)
            self._save_outbound_message(to_phone, message, msg.sid)
            return {"success": True, "sid": msg.sid, "status": msg.status}
        except Exception as e:
            logger.error(f"Twilio WhatsApp send failed: {e}")
            return self._log_fallback("whatsapp", to_phone, message, error=str(e))

    def make_voice_call(self, to_phone: str, message: str, purpose: str = "") -> dict:
        if not self.client or not self.config or not self.config.voice_enabled:
            return self._log_fallback("voice", to_phone, message)
        try:
            from_number = self.config.voice_from_number
            base_url = settings.SITE_URL or "https://healthcare-os.com"
            twiml = f'<Response><Say voice="alice" language="{self.config.voice_language}">{message}</Say></Response>'
            call = self.client.calls.create(
                url=f"{base_url}/api/bots/voice/twiml/?message={message}&language={self.config.voice_language}",
                to=to_phone,
                from_=from_number,
                status_callback=f"{base_url}/api/bots/voice/status/",
                status_callback_event=["completed", "busy", "no-answer", "failed"],
            )
            self._save_voice_call(to_phone, from_number, call.sid, purpose)
            return {"success": True, "sid": call.sid, "status": call.status}
        except Exception as e:
            logger.error(f"Twilio Voice call failed: {e}")
            return self._log_fallback("voice", to_phone, message, error=str(e))

    def send_appointment_reminder(self, patient_phone: str, patient_name: str, appointment_time: str, channel: str = "whatsapp") -> dict:
        message = (
            f"Hi {patient_name}, this is a reminder about your upcoming appointment "
            f"scheduled for {appointment_time}. Please confirm or reschedule if needed. "
            f"Reply 1 to confirm, 2 to reschedule, or call us at our office."
        )
        if channel == "whatsapp":
            return self.send_whatsapp(patient_phone, message)
        else:
            return self.make_voice_call(patient_phone, message, purpose="appointment_reminder")

    def handle_incoming_whatsapp(self, from_phone: str, message_body: str, message_sid: str) -> dict:
        reply = self._process_bot_reply(from_phone, message_body)
        self._save_inbound_message(from_phone, message_body, message_sid)
        if reply:
            self.send_whatsapp(from_phone, reply)
        return {"status": "processed", "reply": reply}

    def _process_bot_reply(self, from_phone: str, message: str) -> str:
        if not self.config or not self.config.auto_reply_enabled:
            return ""
        lower = message.lower().strip()
        if lower in ("1", "confirm", "yes"):
            return "Thank you for confirming your appointment. We look forward to seeing you!"
        elif lower in ("2", "reschedule", "change"):
            return "Please call our office to reschedule or visit our patient portal. We're here to help!"
        elif lower in ("3", "cancel", "stop"):
            return "We're sorry to hear that. Please call our office to cancel or modify your appointment."
        elif "help" in lower or "office" in lower or "hours" in lower:
            return "Our office hours are Monday-Friday 9 AM to 5 PM. You can reach us at our main number."
        elif "bill" in lower or "payment" in lower or "invoice" in lower:
            return "For billing inquiries, please visit our patient portal or call our billing department."
        elif "appointment" in lower:
            return "To book or check an appointment, please call our office or use our online booking system."
        else:
            return self.config.auto_reply_message

    def _save_outbound_message(self, to_phone: str, content: str, sid: str):
        from .models import WhatsAppConversation, WhatsAppMessage
        conv, _ = WhatsAppConversation.objects.get_or_create(
            tenant=self.tenant, customer_phone=to_phone,
            defaults={"status": WhatsAppConversation.Status.ACTIVE},
        )
        WhatsAppMessage.objects.create(
            tenant=self.tenant, conversation=conv,
            direction=WhatsAppMessage.Direction.OUTBOUND,
            content=content, twilio_message_sid=sid,
            is_bot_reply=True,
        )
        conv.message_count = conv.message_count + 1
        conv.save(update_fields=["message_count"])

    def _save_inbound_message(self, from_phone: str, content: str, sid: str):
        from .models import WhatsAppConversation, WhatsAppMessage
        conv, _ = WhatsAppConversation.objects.get_or_create(
            tenant=self.tenant, customer_phone=from_phone,
            defaults={"status": WhatsAppConversation.Status.ACTIVE},
        )
        WhatsAppMessage.objects.create(
            tenant=self.tenant, conversation=conv,
            direction=WhatsAppMessage.Direction.INBOUND,
            content=content, twilio_message_sid=sid,
        )
        conv.message_count = conv.message_count + 1
        conv.last_message_at = timezone.now()
        conv.save(update_fields=["message_count", "last_message_at"])

    def _save_voice_call(self, to_phone: str, from_number: str, sid: str, purpose: str):
        from .models import VoiceCallLog
        VoiceCallLog.objects.create(
            tenant=self.tenant, direction=VoiceCallLog.Direction.OUTBOUND,
            to_number=to_phone, from_number=from_number,
            twilio_call_sid=sid, purpose=purpose, is_bot_call=True,
            status=VoiceCallLog.Status.QUEUED, started_at=timezone.now(),
        )

    def _log_fallback(self, channel: str, to: str, message: str, error: str = "") -> dict:
        logger.info(f"[{channel.upper()} FALLBACK] TO: {to} | MSG: {message[:100]}")
        return {"success": False, "fallback": True, "error": error or "Twilio not configured"}
