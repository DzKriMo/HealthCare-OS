from django.contrib import admin
from .models import TestCatalog, LabOrder, Specimen, LabResult

@admin.register(TestCatalog)
class TestCatalogAdmin(admin.ModelAdmin):
    list_display = ["name","department","specimen_type","price","tenant"]

@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ["patient","status","priority","ordered_at"]

@admin.register(Specimen)
class SpecimenAdmin(admin.ModelAdmin):
    list_display = ["barcode","specimen_type","status","collection_date"]

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ["test","value","flag","status","performed_at"]
