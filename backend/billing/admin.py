"""Django Admin for billing models."""
from django.contrib import admin
from .models import BillingItem, Quote, Invoice, Payment, InsuranceClaim


@admin.register(BillingItem)
class BillingItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "tax_rate", "tenant", "is_active"]
    list_filter = ["category", "is_active", "tenant"]


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["quote_number", "patient", "status", "grand_total", "created_at"]
    list_filter = ["status", "tenant"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "patient", "status", "grand_total", "amount_paid", "balance_due", "issued_date"]
    list_filter = ["status", "tenant"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["patient", "amount", "method", "payment_date", "is_refund"]
    list_filter = ["method", "is_refund", "tenant"]


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ["claim_number", "patient", "status", "claimed_amount", "approved_amount"]
    list_filter = ["status", "tenant"]
