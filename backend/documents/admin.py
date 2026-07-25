from django.contrib import admin
from .models import Document, Signature

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["file_name", "patient", "category", "file_size", "uploaded_at"]
    list_filter = ["category", "tenant"]

@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ["signed_by_name", "patient", "entity_type", "signed_at"]
