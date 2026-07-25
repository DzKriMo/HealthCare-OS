from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import VideoConsultation, ChatRoom, ChatMessage
from . import serializers


@extend_schema(tags=["telemedicine"])
class ConsultationListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.VideoConsultationCreateSerializer
        return serializers.VideoConsultationSerializer

    def get_queryset(self):
        qs = VideoConsultation.objects.for_tenant(self.request.tenant)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        patient = self.request.query_params.get("patient")
        if patient:
            qs = qs.filter(patient_id=patient)
        practitioner = self.request.query_params.get("practitioner")
        if practitioner:
            qs = qs.filter(practitioner_id=practitioner)
        qs = qs.select_related("patient", "practitioner")
        return qs

    def get_required_permission(self):
        return "telemedicine.start" if self.request.method == "POST" else "telemedicine.read"

    def perform_create(self, serializer):
        serializer.save()


@extend_schema(tags=["telemedicine"])
class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        return serializers.VideoConsultationSerializer

    def get_queryset(self):
        return VideoConsultation.objects.for_tenant(self.request.tenant).select_related("patient", "practitioner")

    def get_required_permission(self):
        return "telemedicine.manage"

    def perform_destroy(self, instance):
        instance.status = VideoConsultation.Status.CANCELLED
        instance.save(update_fields=["status"])


@extend_schema(tags=["telemedicine"])
class ConsultationStartView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_queryset(self):
        return VideoConsultation.objects.for_tenant(self.request.tenant)

    def get_required_permission(self):
        return "telemedicine.start"

    def post(self, request, pk):
        try:
            consultation = self.get_queryset().get(pk=pk)
        except VideoConsultation.DoesNotExist:
            raise NotFound("Consultation not found.")
        consultation.status = VideoConsultation.Status.IN_PROGRESS
        consultation.started_at = timezone.now()
        consultation.save(update_fields=["status", "started_at"])
        return Response(serializers.VideoConsultationSerializer(consultation, context={"request": request}).data)


@extend_schema(tags=["telemedicine"])
class ConsultationEndView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_queryset(self):
        return VideoConsultation.objects.for_tenant(self.request.tenant)

    def get_required_permission(self):
        return "telemedicine.manage"

    def post(self, request, pk):
        try:
            consultation = self.get_queryset().get(pk=pk)
        except VideoConsultation.DoesNotExist:
            raise NotFound("Consultation not found.")
        consultation.status = VideoConsultation.Status.COMPLETED
        consultation.ended_at = timezone.now()
        consultation.save(update_fields=["status", "ended_at"])
        return Response(serializers.VideoConsultationSerializer(consultation, context={"request": request}).data)


@extend_schema(tags=["telemedicine"])
class ChatRoomListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.ChatRoomSerializer

    def get_queryset(self):
        user = self.request.user
        qs = ChatRoom.objects.for_tenant(self.request.tenant).filter(participants=user, is_active=True)
        qs = qs.prefetch_related("participants", "messages")
        return qs

    def get_required_permission(self):
        return "telemedicine.chat"


@extend_schema(tags=["telemedicine"])
class ChatMessageListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.ChatMessageCreateSerializer
        return serializers.ChatMessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        room = ChatRoom.objects.for_tenant(self.request.tenant).filter(id=room_id, participants=self.request.user).first()
        if not room:
            raise NotFound("Chat room not found.")
        return ChatMessage.objects.filter(room_id=room_id).select_related("sender")

    def get_required_permission(self):
        return "telemedicine.chat"

    def perform_create(self, serializer):
        serializer.save()


@extend_schema(tags=["telemedicine"])
class ChatMessageMarkReadView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_required_permission(self):
        return "telemedicine.chat"

    def post(self, request, room_id, pk):
        try:
            msg = ChatMessage.objects.get(pk=pk, room_id=room_id)
        except ChatMessage.DoesNotExist:
            raise NotFound("Message not found.")
        msg.mark_read()
        return Response({"status": "ok"})


@extend_schema(tags=["telemedicine"])
class DashboardView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_required_permission(self):
        return "telemedicine.read"

    def get(self, request):
        qs = VideoConsultation.objects.for_tenant(request.tenant)
        now = timezone.now()
        return Response({
            "upcoming": qs.filter(status__in=["scheduled", "ready"], scheduled_at__gte=now).count(),
            "in_progress": qs.filter(status="in_progress").count(),
            "completed_today": qs.filter(
                status="completed",
                ended_at__date=now.date(),
            ).count(),
            "total": qs.count(),
        })
