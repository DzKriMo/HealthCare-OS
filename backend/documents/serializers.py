"""Serializers for documents and signatures."""
from rest_framework import serializers
from .models import Document, Signature


class DocumentSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "patient", "file_name", "file_size", "size_display",
            "mime_type", "category", "tags", "description",
            "version", "is_archived", "is_sensitive",
            "width", "height",
            "uploaded_by", "uploaded_by_name", "uploaded_at",
            "download_url",
        ]
        read_only_fields = [
            "id", "file_size", "storage_path", "file_hash",
            "version", "uploaded_by", "uploaded_at",
        ]

    def get_download_url(self, obj) -> str | None:
        """Generate a signed URL for download (placeholder — actual S3 signed URL)."""
        return f"/api/documents/{obj.id}/download/"


class DocumentUploadSerializer(serializers.Serializer):
    """Handle file upload with metadata."""
    file = serializers.FileField()
    patient_id = serializers.UUIDField(required=False, allow_null=True)
    category = serializers.ChoiceField(choices=Document.Category.choices, default="other")
    tags = serializers.JSONField(required=False, default=list)
    description = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    is_sensitive = serializers.BooleanField(default=False)


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        fields = [
            "id", "patient", "svg_data",
            "entity_type", "entity_id",
            "signed_by_name", "signed_at",
        ]
        read_only_fields = ["id", "signed_at"]


class SignatureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        fields = [
            "patient", "svg_data", "entity_type", "entity_id",
            "signed_by_name",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        request = self.context["request"]
        return Signature.objects.create(
            tenant=tenant,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            **validated_data,
        )
