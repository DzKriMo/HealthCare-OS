"""
Document views — upload, download, list, categorize, sign.
"""
import uuid
import hashlib
from django.http import FileResponse, Http404
from rest_framework import generics, status, views, parsers
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from patients.models import Patient
from .models import Document, Signature
from . import serializers


# ═══════════════════════════════════════════════════════════════
# Documents
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["documents"])
class DocumentListView(generics.ListCreateAPIView):
    """List documents for a patient or general. Create via upload."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.DocumentUploadSerializer
        return serializers.DocumentSerializer

    def get_queryset(self):
        qs = Document.objects.for_tenant(self.request.tenant).filter(is_archived=False)
        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs.select_related("uploaded_by")

    def get_required_permission(self):
        return "documents.upload" if self.request.method == "POST" else "documents.read"

    def create(self, request, *args, **kwargs):
        """Handle file upload with metadata."""
        upload_serializer = serializers.DocumentUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        uploaded_file = upload_serializer.validated_data["file"]
        patient_id = upload_serializer.validated_data.get("patient_id")
        category = upload_serializer.validated_data.get("category", "other")

        # Generate tenant-scoped storage path
        patient_segment = f"patients/{patient_id}" if patient_id else "general"
        file_id = uuid.uuid4()
        ext = uploaded_file.name.rsplit(".", 1)[-1] if "." in uploaded_file.name else "bin"
        storage_path = f"{request.tenant.slug}/{patient_segment}/{category}/{file_id}.{ext}"

        # Compute hash
        file_data = uploaded_file.read()
        file_hash = hashlib.sha256(file_data).hexdigest()

        # In production: upload to MinIO/S3 using boto3
        # For dev: store locally
        import os
        from django.conf import settings
        local_dir = os.path.join(settings.BASE_DIR, "media", "documents",
                                 request.tenant.slug, patient_segment, category)
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, f"{file_id}.{ext}")
        with open(local_path, "wb") as f:
            f.write(file_data)

        # Verify patient belongs to tenant
        if patient_id:
            try:
                Patient.objects.for_tenant(request.tenant).get(pk=patient_id)
            except Patient.DoesNotExist:
                return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        document = Document.objects.create(
            tenant=request.tenant,
            patient_id=patient_id,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type or "application/octet-stream",
            storage_path=storage_path,
            file_hash=file_hash,
            category=category,
            tags=upload_serializer.validated_data.get("tags", []),
            description=upload_serializer.validated_data.get("description", ""),
            is_sensitive=upload_serializer.validated_data.get("is_sensitive", False),
            uploaded_by=request.user,
        )

        return Response(
            serializers.DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["documents"])
class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """Get document metadata or archive it."""
    serializer_class = serializers.DocumentSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_queryset(self):
        return Document.objects.for_tenant(self.request.tenant)

    def get_required_permission(self):
        return "documents.delete" if self.request.method == "DELETE" else "documents.read"

    def perform_destroy(self, instance):
        instance.is_archived = True
        instance.save(update_fields=["is_archived"])


@extend_schema(tags=["documents"], summary="Download file")
class DocumentDownloadView(generics.GenericAPIView):
    """Download a document by ID. Generates a redirect to signed URL in production."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "documents.read"

    def get(self, request, pk):
        try:
            doc = Document.objects.for_tenant(request.tenant).get(pk=pk)
        except Document.DoesNotExist:
            raise NotFound("Document not found.")

        # In production: generate pre-signed S3 URL and redirect
        # For dev: serve local file
        import os
        from django.conf import settings
        local_path = os.path.join(settings.BASE_DIR, "media", "documents", doc.storage_path)
        if os.path.exists(local_path):
            response = FileResponse(
                open(local_path, "rb"),
                content_type=doc.mime_type,
                as_attachment=True,
                filename=doc.file_name,
            )
            response["Content-Disposition"] = f'attachment; filename="{doc.file_name}"'
            return response

        raise Http404("File not found on storage.")


# ═══════════════════════════════════════════════════════════════
# Signatures
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["documents"])
class SignatureListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.SignatureCreateSerializer
        return serializers.SignatureSerializer

    def get_queryset(self):
        qs = Signature.objects.for_tenant(self.request.tenant)
        entity_type = self.request.query_params.get("entity_type")
        entity_id = self.request.query_params.get("entity_id")
        if entity_type and entity_id:
            qs = qs.filter(entity_type=entity_type, entity_id=entity_id)
        return qs

    def get_required_permission(self):
        return "documents.upload" if self.request.method == "POST" else "documents.read"
