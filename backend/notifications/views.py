"""
Notification views — templates, events, dispatch, channel config.
"""
from django.db import models as db_models
from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import NotificationTemplate, NotificationEvent, NotificationChannelConfig
from .backends import orchestrator
from . import serializers


# ═══════════════════════════════════════════════════════════════
# Templates
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["notifications"])
class TemplateListView(generics.ListCreateAPIView):
    serializer_class = serializers.NotificationTemplateSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "notifications.manage_templates"

    def get_queryset(self):
        qs = NotificationTemplate.objects.filter(is_active=True)
        return qs.filter(
            db_models.Q(tenant=self.request.tenant) | db_models.Q(tenant__isnull=True),
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["notifications"])
class TemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.NotificationTemplateSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "notifications.manage_templates"

    def get_queryset(self):
        return NotificationTemplate.objects.filter(tenant=self.request.tenant)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


# ═══════════════════════════════════════════════════════════════
# Events & Send
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["notifications"])
class EventListView(generics.ListAPIView):
    """View notification event history."""
    serializer_class = serializers.NotificationEventSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "notifications.send"

    def get_queryset(self):
        return NotificationEvent.objects.for_tenant(self.request.tenant)


@extend_schema(tags=["notifications"], summary="Send a notification")
class NotificationSendView(generics.GenericAPIView):
    """Manually dispatch a notification."""
    serializer_class = serializers.NotificationSendSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "notifications.send"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        event = orchestrator.dispatch(
            tenant=request.tenant,
            event_type=data["event_type"],
            channel=data["channel"],
            recipient_email=data.get("recipient_email", ""),
            recipient_phone=data.get("recipient_phone", ""),
            recipient_name=data.get("recipient_name", ""),
            context=data.get("context", {}),
        )

        return Response(
            serializers.NotificationEventSerializer(event).data,
            status=status.HTTP_201_CREATED if event.status == "sent" else status.HTTP_200_OK,
        )


# ═══════════════════════════════════════════════════════════════
# Channel Config
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["notifications"])
class ChannelConfigView(generics.RetrieveUpdateAPIView):
    """Get or update tenant notification channel configuration."""
    serializer_class = serializers.ChannelConfigSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "notifications.manage_templates"

    def get_object(self):
        config, _ = NotificationChannelConfig.objects.get_or_create(
            tenant=self.request.tenant,
        )
        return config
