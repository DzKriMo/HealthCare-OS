from django.contrib import admin; from .models import CancerStaging, ChemotherapyProtocol, TumorMarker
@admin.register(CancerStaging)
class StagingAdmin(admin.ModelAdmin): list_display = ["patient","diagnosis","stage","diagnosis_date"]
@admin.register(ChemotherapyProtocol)
class ChemoAdmin(admin.ModelAdmin): list_display = ["patient","protocol_name","cycle_number","status"]
@admin.register(TumorMarker)
class TumorMarkerAdmin(admin.ModelAdmin): list_display = ["patient","marker_name","value","measured_date"]
