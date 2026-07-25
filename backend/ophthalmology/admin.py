from django.contrib import admin
from .models import EyeExam, VisionTest, LensPrescription

@admin.register(EyeExam)
class EyeExamAdmin(admin.ModelAdmin): list_display = ["patient","exam_date","va_od_best","va_os_best"]
@admin.register(VisionTest)
class VisionTestAdmin(admin.ModelAdmin): list_display = ["exam","test_type"]
@admin.register(LensPrescription)
class LensPrescriptionAdmin(admin.ModelAdmin): list_display = ["patient","prescription_type","prescribed_date"]
