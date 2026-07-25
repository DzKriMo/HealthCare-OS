from rest_framework import serializers; from .models import CancerStaging, ChemotherapyProtocol, TumorMarker

class StagingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta: model = CancerStaging; fields = ["id","patient","diagnosis","tnm_t","tnm_n","tnm_m","stage","diagnosis_date","notes"]; read_only_fields = ["id","recorded_by"]

class ChemoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta: model = ChemotherapyProtocol; fields = ["id","patient","protocol_name","drugs","cycle_number","total_cycles","start_date","status","notes"]; read_only_fields = ["id","prescribed_by"]

class TumorMarkerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta: model = TumorMarker; fields = ["id","patient","marker_name","value","unit","reference_range","measured_date","notes"]; read_only_fields = ["id"]
