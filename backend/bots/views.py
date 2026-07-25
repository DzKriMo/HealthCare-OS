import json
import logging
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

logger = logging.getLogger("healthcare_os.bots")

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import BotConfig, WhatsAppConversation, WhatsAppMessage, VoiceCallLog
from . import serializers
from .services import TwilioService


@extend_schema(tags=["bots"])
class BotConfigView(generics.RetrieveUpdateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.BotConfigSerializer

    def get_required_permission(self):
        return "bots.manage"

    def get_object(self):
        obj, _ = BotConfig.objects.get_or_create(tenant=self.request.tenant)
        return obj


@extend_schema(tags=["bots"])
class WhatsAppSendView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.WhatsAppSendSerializer

    def get_required_permission(self):
        return "bots.send_whatsapp"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = TwilioService(request.tenant)
        result = service.send_whatsapp(
            serializer.validated_data["to_phone"],
            serializer.validated_data["message"],
        )
        return Response(result)


@extend_schema(tags=["bots"])
class VoiceCallView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.VoiceCallSerializer

    def get_required_permission(self):
        return "bots.make_call"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = TwilioService(request.tenant)
        result = service.make_voice_call(
            serializer.validated_data["to_phone"],
            serializer.validated_data["message"],
            serializer.validated_data.get("purpose", ""),
        )
        return Response(result)


@extend_schema(tags=["bots"])
class AppointmentReminderView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.AppointmentReminderSerializer

    def get_required_permission(self):
        return "bots.send_reminder"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = TwilioService(request.tenant)
        result = service.send_appointment_reminder(
            serializer.validated_data["patient_phone"],
            serializer.validated_data["patient_name"],
            serializer.validated_data["appointment_time"],
            serializer.validated_data.get("channel", "whatsapp"),
        )
        return Response(result)


@extend_schema(tags=["bots"])
class ConversationListView(generics.ListAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.WhatsAppConversationSerializer

    def get_required_permission(self):
        return "bots.read_conversations"

    def get_queryset(self):
        qs = WhatsAppConversation.objects.for_tenant(self.request.tenant)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        phone = self.request.query_params.get("phone")
        if phone:
            qs = qs.filter(customer_phone__icontains=phone)
        return qs.prefetch_related("messages").order_by("-last_message_at")


@extend_schema(tags=["bots"])
class ConversationDetailView(generics.RetrieveAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.WhatsAppConversationDetailSerializer

    def get_required_permission(self):
        return "bots.read_conversations"

    def get_queryset(self):
        return WhatsAppConversation.objects.for_tenant(self.request.tenant).prefetch_related("messages__sender")


@extend_schema(tags=["bots"])
class ConversationMessageListView(generics.ListAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.WhatsAppMessageSerializer

    def get_required_permission(self):
        return "bots.read_conversations"

    def get_queryset(self):
        conv_id = self.kwargs["pk"]
        return WhatsAppMessage.objects.for_tenant(self.request.tenant).filter(conversation_id=conv_id)


@extend_schema(tags=["bots"])
class VoiceCallLogListView(generics.ListAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.VoiceCallLogSerializer

    def get_required_permission(self):
        return "bots.read_calls"

    def get_queryset(self):
        qs = VoiceCallLog.objects.for_tenant(self.request.tenant)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


@extend_schema(tags=["bots"])
class DashboardView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_required_permission(self):
        return "bots.read"

    def get(self, request):
        conversations = WhatsAppConversation.objects.for_tenant(request.tenant)
        calls = VoiceCallLog.objects.for_tenant(request.tenant)
        now = timezone.localtime(timezone.now())
        return Response({
            "active_conversations": conversations.filter(status="active").count(),
            "total_conversations": conversations.count(),
            "total_messages": sum(conversations.values_list("message_count", flat=True)),
            "calls_today": calls.filter(started_at__date=now.date()).count(),
            "total_calls": calls.count(),
            "successful_calls": calls.filter(status="completed").count(),
        })


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "healthcare-os-verify")
        if mode == "subscribe" and token == verify_token:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    def post(self, request):
        try:
            body = json.loads(request.body)
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        from_phone = msg.get("from", "")
                        text = msg.get("text", {}).get("body", "")
                        msg_id = msg.get("id", "")
                        tenant = self._resolve_tenant(from_phone)
                        if tenant:
                            service = TwilioService(tenant)
                            service.handle_incoming_whatsapp(from_phone, text, msg_id)
            return JsonResponse({"status": "ok"})
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {e}")
            return JsonResponse({"status": "error"}, status=500)

    def _resolve_tenant(self, phone):
        from .models import BotConfig
        config = BotConfig.objects.filter(whatsapp_enabled=True).select_related("tenant").first()
        return config.tenant if config else None


@method_decorator(csrf_exempt, name="dispatch")
class VoiceTwimlView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        message = request.GET.get("message", "Hello from Healthcare OS")
        language = request.GET.get("language", "en-US")
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice" language="{language}">{message}</Say></Response>'
        return HttpResponse(twiml, content_type="text/xml")


@method_decorator(csrf_exempt, name="dispatch")
class VoiceStatusView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        call_sid = request.POST.get("CallSid", "")
        status = request.POST.get("CallStatus", "")
        duration = request.POST.get("CallDuration", "")
        try:
            log = VoiceCallLog.objects.get(twilio_call_sid=call_sid)
            log.status = status
            if duration:
                log.duration_seconds = int(duration)
            if status == "completed":
                log.ended_at = timezone.now()
            log.save(update_fields=["status", "duration_seconds", "ended_at"])
        except VoiceCallLog.DoesNotExist:
            pass
        return JsonResponse({"status": "ok"})
