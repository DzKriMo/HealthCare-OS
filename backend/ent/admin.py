from django.contrib import admin
from .models import AudiologyExam, EndoscopyRecord

@admin.register(AudiologyExam)
class AudiologyAdmin(admin.ModelAdmin): list_display = ["patient","exam_date","test_type","hearing_loss_type"]
@admin.register(EndoscopyRecord)
class EndoscopyAdmin(admin.ModelAdmin): list_display = ["patient","procedure_date","endoscopy_type"]
