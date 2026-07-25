from rest_framework import serializers
from .models import EyeExam, VisionTest, LensPrescription


class EyeExamSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)

    class Meta:
        model = EyeExam
        fields = ["id","patient","patient_name","exam_date","reason",
                  "va_od_unaided","va_os_unaided","va_od_best","va_os_best",
                  "refraction_od_sphere","refraction_od_cylinder","refraction_od_axis",
                  "refraction_os_sphere","refraction_os_cylinder","refraction_os_axis",
                  "iop_od","iop_os","slit_lamp_findings","fundus_findings","assessment","plan",
                  "practitioner","practitioner_name","created_at"]
        read_only_fields = ["id","practitioner","created_at"]


class LensPrescriptionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = LensPrescription
        fields = ["id","patient","exam","prescription_type",
                  "od_sphere","od_cylinder","od_axis","od_add",
                  "os_sphere","os_cylinder","os_axis","os_add","pd","notes","prescribed_date"]
        read_only_fields = ["id","prescribed_by"]
