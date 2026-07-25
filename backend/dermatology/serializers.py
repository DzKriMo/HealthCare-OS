from rest_framework import serializers
from .models import BodyMap, Lesion, LesionPhoto, DermatologyProcedure


class LesionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LesionPhoto
        fields = ["id","image_path","taken_date","notes","dermoscopy"]
        read_only_fields = ["id"]

class LesionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    photos = LesionPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Lesion
        fields = ["id","body_map","patient","name","body_region","location_detail","size_mm","color","morphology",
                  "border","dermoscopy_findings","clinical_impression","is_biopsied","biopsy_result","is_active",
                  "discovered_date","photos","created_at"]
        read_only_fields = ["id","patient","body_map","recorded_by","created_at"]

class BodyMapSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    lesions = LesionSerializer(many=True, read_only=True)

    class Meta:
        model = BodyMap
        fields = ["id","patient","patient_name","notes","lesions","updated_at"]
        read_only_fields = ["id","updated_at"]

class ProcedureSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = DermatologyProcedure
        fields = ["id","patient","lesion","procedure_type","description","performed_date","performed_by"]
        read_only_fields = ["id","performed_by"]
