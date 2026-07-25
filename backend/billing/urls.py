"""Billing URL configuration."""
from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    # Billing items (catalog)
    path("items/", views.BillingItemListView.as_view(), name="item-list"),
    path("items/<uuid:pk>/", views.BillingItemDetailView.as_view(), name="item-detail"),

    # Quotes
    path("quotes/", views.QuoteListView.as_view(), name="quote-list"),
    path("quotes/<uuid:pk>/", views.QuoteDetailView.as_view(), name="quote-detail"),
    path("quotes/<uuid:pk>/convert/", views.QuoteConvertView.as_view(), name="quote-convert"),

    # Invoices
    path("invoices/", views.InvoiceListView.as_view(), name="invoice-list"),
    path("invoices/<uuid:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<uuid:pk>/issue/", views.InvoiceIssueView.as_view(), name="invoice-issue"),

    # Payments
    path("payments/", views.PaymentListView.as_view(), name="payment-list"),
    path("payments/<uuid:payment_pk>/refund/", views.RefundView.as_view(), name="payment-refund"),

    # POS
    path("pos/checkout/", views.POSCheckoutView.as_view(), name="pos-checkout"),

    # Revenue
    path("revenue/", views.RevenueDashboardView.as_view(), name="revenue"),

    # Insurance claims
    path("claims/", views.InsuranceClaimListView.as_view(), name="claim-list"),
    path("claims/<uuid:pk>/", views.InsuranceClaimDetailView.as_view(), name="claim-detail"),

    # Online payments
    path("checkout/", views.CheckoutSessionView.as_view(), name="checkout"),
    path("stripe-webhook/", views.StripeWebhookView.as_view(), name="stripe-webhook"),
]
