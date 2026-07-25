from django.contrib import admin; from .models import AnimalRecord, RabiesCertificate
@admin.register(AnimalRecord)
class AnimalRecordAdmin(admin.ModelAdmin): list_display = ["patient","species","breed","microchip_number"]
@admin.register(RabiesCertificate)
class RabiesCertAdmin(admin.ModelAdmin): list_display = ["patient","vaccine_name","administered_date","expiration_date"]
