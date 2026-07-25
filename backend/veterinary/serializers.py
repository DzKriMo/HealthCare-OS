from rest_framework import serializers; from .models import AnimalRecord, RabiesCertificate

class AnimalRecordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta: model = AnimalRecord; fields = ["id","patient","species","breed","sex","color","date_of_birth","weight_kg","microchip_number","notes"]; read_only_fields = ["id","created_at"]

class RabiesCertSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    class Meta: model = RabiesCertificate; fields = ["id","patient","vaccine_name","lot_number","administered_date","expiration_date","veterinarian","certificate_number","notes"]; read_only_fields = ["id"]
