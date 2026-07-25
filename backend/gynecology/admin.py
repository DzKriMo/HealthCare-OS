from django.contrib import admin
from .models import OBHistory, PapSmear, AntenatalVisit

@admin.register(OBHistory)
class OBHistoryAdmin(admin.ModelAdmin): list_display = ["patient","gravida","para","lmp"]
@admin.register(PapSmear)
class PapSmearAdmin(admin.ModelAdmin): list_display = ["patient","performed_date","result"]
@admin.register(AntenatalVisit)
class AntenatalAdmin(admin.ModelAdmin): list_display = ["patient","visit_date","gestational_weeks","fetal_hr"]
