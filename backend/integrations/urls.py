from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("api-keys/", views.ApiKeyListView.as_view(), name="api-key-list"),
    path("api-keys/<uuid:pk>/revoke/", views.ApiKeyRevokeView.as_view(), name="api-key-revoke"),
    path("webhooks/", views.WebhookListView.as_view(), name="webhook-list"),
    path("webhooks/<uuid:pk>/", views.WebhookDetailView.as_view(), name="webhook-detail"),
    path("payment-configs/", views.PaymentConfigListView.as_view(), name="payment-configs"),
    path("calendar-configs/", views.CalendarConfigListView.as_view(), name="calendar-configs"),
    path("comm-configs/", views.CommunicationConfigListView.as_view(), name="comm-configs"),
    path("clearinghouses/", views.ClearinghouseConfigView.as_view(), name="clearinghouses"),
    path("edi-claims/", views.EDIClaimListView.as_view(), name="edi-claims"),
    path("accounting/", views.AccountingConfigView.as_view(), name="accounting"),
    path("government/", views.GovernmentConnectorView.as_view(), name="government"),
    path("marketplace/", views.PluginCatalogView.as_view(), name="plugin-catalog"),
    path("marketplace/installed/", views.PluginInstallView.as_view(), name="plugin-install"),
    path("marketplace/<uuid:plugin_pk>/reviews/", views.PluginReviewView.as_view(), name="plugin-reviews"),
]
