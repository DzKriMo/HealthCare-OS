from django.contrib import admin
from .models import ECGRecord, EchoReport, BPReading, CVRiskScore

@admin.register(ECGRecord)
class ECGRecordAdmin(admin.ModelAdmin): list_display = ["patient","performed_date","rhythm","is_abnormal"]
@admin.register(EchoReport)
class EchoReportAdmin(admin.ModelAdmin): list_display = ["patient","study_date","lvef"]
@admin.register(BPReading)
class BPReadingAdmin(admin.ModelAdmin): list_display = ["patient","systolic","diastolic","recorded_at"]
@admin.register(CVRiskScore)
class CVRiskScoreAdmin(admin.ModelAdmin): list_display = ["patient","score_type","risk_percentage","risk_category"]
