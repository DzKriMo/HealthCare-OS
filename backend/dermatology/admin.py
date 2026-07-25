from django.contrib import admin
from .models import BodyMap, Lesion, LesionPhoto, DermatologyProcedure

@admin.register(BodyMap)
class BodyMapAdmin(admin.ModelAdmin): list_display = ["patient"]
@admin.register(Lesion)
class LesionAdmin(admin.ModelAdmin): list_display = ["name","body_region","patient","is_active"]
@admin.register(LesionPhoto)
class LesionPhotoAdmin(admin.ModelAdmin): list_display = ["lesion","taken_date","dermoscopy"]
@admin.register(DermatologyProcedure)
class DermatologyProcedureAdmin(admin.ModelAdmin): list_display = ["patient","procedure_type","performed_date"]
