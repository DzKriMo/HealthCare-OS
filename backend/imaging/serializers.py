"""Serializers for imaging module."""
from rest_framework import serializers
from .models import ImagingStudy, ImagingSeries, ImagingImage, RadiologyReport


class ImagingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingImage
        fields = ["id","image_number","sop_instance_uid","mime_type","file_size","width","height","slice_location"]
        read_only_fields = ["id"]


class ImagingSeriesSerializer(serializers.ModelSerializer):
    images = ImagingImageSerializer(many=True, read_only=True)

    class Meta:
        model = ImagingSeries
        fields = ["id","series_uid","series_number","modality","description","body_part","image_count","images"]
        read_only_fields = ["id"]


class ImagingStudyListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    report_status = serializers.SerializerMethodField()
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ImagingStudy
        fields = ["id","patient","patient_name","accession_number","modality","body_part","status","priority","performed_at","report_status"]
        read_only_fields = ["id","status","report_status"]

    def get_report_status(self, obj):
        if hasattr(obj, "report"): return obj.report.status
        return None


class RadiologyReportSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    study_summary = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    signed_by_name = serializers.CharField(source="signed_by.full_name", read_only=True)

    class Meta:
        model = RadiologyReport
        fields = ["id","study","study_summary","findings","impression","recommendations","comparison_study",
                  "status","author","author_name","signed_by","signed_by_name","signed_at","created_at"]
        read_only_fields = ["id","status","author","signed_by","signed_at","created_at"]

    def get_study_summary(self, obj):
        return f"{obj.study.get_modality_display()} — {obj.study.body_part}"


class ReportCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = RadiologyReport
        fields = ["id","study","findings","impression","recommendations","comparison_study"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return RadiologyReport.objects.create(tenant=tenant, author=user, **validated_data)


class StudyCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ImagingStudy
        fields = ["id","patient","modality","body_part","protocol","priority","reason","appointment","accession_number"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        import secrets, uuid
        return ImagingStudy.objects.create(
            tenant=tenant, ordered_by=user,
            study_uid=f"1.2.840.{uuid.uuid4().hex[:16]}.{secrets.token_hex(4)}",
            **validated_data,
        )
