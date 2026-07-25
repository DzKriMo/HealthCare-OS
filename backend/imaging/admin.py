from django.contrib import admin
from .models import ImagingStudy, ImagingSeries, ImagingImage, RadiologyReport

@admin.register(ImagingStudy)
class ImagingStudyAdmin(admin.ModelAdmin):
    list_display = ["patient","modality","body_part","status","performed_at"]

@admin.register(ImagingSeries)
class ImagingSeriesAdmin(admin.ModelAdmin):
    list_display = ["study","series_number","modality","description"]

@admin.register(ImagingImage)
class ImagingImageAdmin(admin.ModelAdmin):
    list_display = ["series","image_number","sop_instance_uid"]

@admin.register(RadiologyReport)
class RadiologyReportAdmin(admin.ModelAdmin):
    list_display = ["study","status","author","signed_at"]
