"""Integration views — webhooks and API key management."""
from django.db import models as db_models
from rest_framework import generics, status, views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import (WebhookEndpoint, WebhookDelivery, PaymentProviderConfig,
    CalendarProviderConfig, CommunicationProviderConfig,
    InsuranceClearinghouseConfig, EDIClaimSubmission, EligibilityCheck,
    AccountingProviderConfig, GovernmentConnectorConfig,
    Plugin, PluginInstallation, PluginReview)
from identity.apikey import ApiKey


# ═══════════════════════════════════════════════════════════════
# API Keys
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["integrations"])
class ApiKeyListView(generics.ListCreateAPIView, views.APIView):
    """List or create API keys for the tenant."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "integrations.manage"

    def get(self, request):
        keys = ApiKey.objects.filter(tenant=request.tenant).values(
            "id", "name", "prefix", "scopes", "rate_limit",
            "is_active", "last_used_at", "created_at", "expires_at",
        )
        return Response(list(keys))

    def post(self, request):
        name = request.data.get("name", "")
        scopes = request.data.get("scopes", [])
        rate_limit = request.data.get("rate_limit", "100/hour")

        if not name:
            return Response({"error": "name is required."}, status=status.HTTP_400_BAD_REQUEST)

        api_key, full_key = ApiKey.generate(
            tenant=request.tenant,
            name=name,
            scopes=scopes,
            created_by=request.user,
            rate_limit=rate_limit,
        )

        return Response({
            "id": str(api_key.id),
            "name": api_key.name,
            "prefix": api_key.prefix,
            "key": full_key,  # Only shown once!
            "scopes": api_key.scopes,
            "created_at": api_key.created_at,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=["integrations"])
class ApiKeyRevokeView(views.APIView):
    """Revoke an API key."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "integrations.manage"

    def post(self, request, pk):
        try:
            key = ApiKey.objects.get(pk=pk, tenant=request.tenant)
        except ApiKey.DoesNotExist:
            return Response({"error": "API key not found."}, status=status.HTTP_404_NOT_FOUND)

        key.is_active = False
        key.save(update_fields=["is_active"])
        return Response({"message": "API key revoked."})


# ═══════════════════════════════════════════════════════════════
# Webhooks
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["integrations"])
class WebhookListView(generics.ListCreateAPIView, views.APIView):
    """List or register webhook endpoints."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "integrations.manage"

    def get(self, request):
        webhooks = WebhookEndpoint.objects.filter(tenant=request.tenant).values(
            "id", "name", "url", "events", "is_active", "created_at",
        )
        return Response(list(webhooks))

    def post(self, request):
        name = request.data.get("name", "")
        url = request.data.get("url", "")
        events = request.data.get("events", [])
        secret = request.data.get("secret", "")

        if not name or not url:
            return Response({"error": "name and url are required."}, status=status.HTTP_400_BAD_REQUEST)

        import secrets as sec
        webhook = WebhookEndpoint.objects.create(
            tenant=request.tenant,
            name=name,
            url=url,
            secret=secret or sec.token_hex(32),
            events=events,
        )

        return Response({
            "id": str(webhook.id),
            "name": webhook.name,
            "url": webhook.url,
            "secret": webhook.secret,
            "events": webhook.events,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=["integrations"])
class WebhookDetailView(views.APIView):
    """Get webhook details or toggle active status."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "integrations.manage"

    def get(self, request, pk):
        try:
            webhook = WebhookEndpoint.objects.get(pk=pk, tenant=request.tenant)
        except WebhookEndpoint.DoesNotExist:
            return Response({"error": "Webhook not found."}, status=status.HTTP_404_NOT_FOUND)

        deliveries = WebhookDelivery.objects.filter(webhook=webhook)[:10].values(
            "id", "event_type", "status", "attempts", "response_status", "created_at",
        )

        return Response({
            "id": str(webhook.id),
            "name": webhook.name,
            "url": webhook.url,
            "events": webhook.events,
            "is_active": webhook.is_active,
            "recent_deliveries": list(deliveries),
        })

    def delete(self, request, pk):
        try:
            webhook = WebhookEndpoint.objects.get(pk=pk, tenant=request.tenant)
        except WebhookEndpoint.DoesNotExist:
            return Response({"error": "Webhook not found."}, status=status.HTTP_404_NOT_FOUND)

        webhook.is_active = False
        webhook.save(update_fields=["is_active"])
        return Response({"message": "Webhook deactivated."})


# ═══════════════════════════════════════════════════════════════
# Payment Provider Configs — Sprint B10
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["integrations"])
class PaymentConfigListView(views.APIView):
    """List or configure payment providers for the tenant."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "integrations.manage"

    def get(self, request):
        configs = PaymentProviderConfig.objects.filter(tenant=request.tenant).values(
            "id","provider","is_enabled","is_test_mode","supported_currencies","public_key","created_at",
        )
        return Response(list(configs))

    def post(self, request):
        provider = request.data.get("provider")
        if not provider: return Response({"error":"provider required"}, status=400)
        cfg, _ = PaymentProviderConfig.objects.update_or_create(
            tenant=request.tenant, provider=provider,
            defaults={
                "is_enabled": request.data.get("is_enabled", False),
                "is_test_mode": request.data.get("is_test_mode", True),
                "api_key": request.data.get("api_key", ""),
                "api_secret": request.data.get("api_secret", ""),
                "webhook_secret": request.data.get("webhook_secret", ""),
                "public_key": request.data.get("public_key", ""),
                "supported_currencies": request.data.get("supported_currencies", ["USD"]),
            },
        )
        return Response({"id":str(cfg.id),"provider":cfg.provider,"is_enabled":cfg.is_enabled}, status=201)


# ═══════════════════════════════════════════════════════════════
# Calendar Provider Configs
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["integrations"])
class CalendarConfigListView(views.APIView):
    """List or configure calendar sync providers."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "integrations.manage"

    def get(self, request):
        configs = CalendarProviderConfig.objects.filter(tenant=request.tenant).values(
            "id","provider","is_enabled","sync_direction","calendar_id","last_synced_at",
        )
        return Response(list(configs))

    def post(self, request):
        provider = request.data.get("provider")
        if not provider: return Response({"error":"provider required"}, status=400)
        cfg, _ = CalendarProviderConfig.objects.update_or_create(
            tenant=request.tenant, provider=provider,
            defaults={
                "is_enabled": request.data.get("is_enabled", False),
                "sync_direction": request.data.get("sync_direction", "two_way"),
                "client_id": request.data.get("client_id", ""),
                "client_secret": request.data.get("client_secret", ""),
                "refresh_token": request.data.get("refresh_token", ""),
                "calendar_id": request.data.get("calendar_id", ""),
            },
        )
        return Response({"id":str(cfg.id),"provider":cfg.provider,"is_enabled":cfg.is_enabled}, status=201)


# ═══════════════════════════════════════════════════════════════
# Communication Provider Configs
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["integrations"])
class CommunicationConfigListView(views.APIView):
    """List or configure communication providers (SMS, WhatsApp, Email)."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "integrations.manage"

    def get(self, request):
        configs = CommunicationProviderConfig.objects.filter(tenant=request.tenant).values(
            "id","channel","provider_name","is_enabled","from_number","from_email","daily_limit",
        )
        return Response(list(configs))

    def post(self, request):
        channel = request.data.get("channel"); provider_name = request.data.get("provider_name")
        if not channel or not provider_name: return Response({"error":"channel and provider_name required"}, status=400)
        cfg, _ = CommunicationProviderConfig.objects.update_or_create(
            tenant=request.tenant, channel=channel, provider_name=provider_name,
            defaults={
                "is_enabled": request.data.get("is_enabled", False),
                "api_key": request.data.get("api_key", ""),
                "api_secret": request.data.get("api_secret", ""),
                "from_number": request.data.get("from_number", ""),
                "from_email": request.data.get("from_email", ""),
                "webhook_secret": request.data.get("webhook_secret", ""),
                "daily_limit": request.data.get("daily_limit", 100),
            },
        )
        return Response({"id":str(cfg.id),"channel":cfg.channel,"provider_name":cfg.provider_name,"is_enabled":cfg.is_enabled}, status=201)


# Insurance EDI — Sprint B11

@extend_schema(tags=["integrations"])
class ClearinghouseConfigView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "integrations.manage"
    def get(self, request):
        configs = InsuranceClearinghouseConfig.objects.filter(tenant=request.tenant).values()
        return Response(list(configs))
    def post(self, request):
        name = request.data.get("name",""); cfg, _ = InsuranceClearinghouseConfig.objects.update_or_create(
            tenant=request.tenant, name=name,
            defaults={"is_enabled":request.data.get("is_enabled",False),"is_test_mode":request.data.get("is_test_mode",True),
                      "ftp_host":request.data.get("ftp_host",""),"api_endpoint":request.data.get("api_endpoint",""),
                      "api_key":request.data.get("api_key",""),"sender_id":request.data.get("sender_id",""),
                      "receiver_id":request.data.get("receiver_id",""),"supported_transactions":request.data.get("supported_transactions",[])},
        )
        return Response({"id":str(cfg.id),"name":cfg.name,"is_enabled":cfg.is_enabled}, status=201)


@extend_schema(tags=["integrations"])
class EDIClaimListView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "integrations.manage"
    def get(self, request):
        claims = EDIClaimSubmission.objects.for_tenant(request.tenant).values("id","claim_number","status","transaction_type","submitted_amount","paid_amount","submitted_at")
        return Response(list(claims))
    def post(self, request):
        import secrets
        claim = EDIClaimSubmission.objects.create(
            tenant=request.tenant, claim_number=f"EDI-{secrets.token_hex(4).upper()}",
            invoice_id=request.data.get("invoice_id"), patient_id=request.data.get("patient_id"),
            transaction_type=request.data.get("transaction_type","837P"),
            submitted_amount=request.data.get("submitted_amount"), clearinghouse_id=request.data.get("clearinghouse_id"),
        )
        return Response({"id":str(claim.id),"claim_number":claim.claim_number,"status":claim.status}, status=201)


@extend_schema(tags=["integrations"])
class AccountingConfigView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "integrations.manage"
    def get(self, request):
        configs = AccountingProviderConfig.objects.filter(tenant=request.tenant).values()
        return Response(list(configs))
    def post(self, request):
        provider = request.data.get("provider",""); cfg, _ = AccountingProviderConfig.objects.update_or_create(
            tenant=request.tenant, provider=provider,
            defaults={"is_enabled":request.data.get("is_enabled",False),"client_id":request.data.get("client_id",""),
                      "client_secret":request.data.get("client_secret",""),"realm_id":request.data.get("realm_id",""),
                      "chart_of_accounts_map":request.data.get("chart_of_accounts_map",{})},
        )
        return Response({"id":str(cfg.id),"provider":cfg.provider,"is_enabled":cfg.is_enabled}, status=201)


@extend_schema(tags=["integrations"])
class GovernmentConnectorView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "integrations.manage"
    def get(self, request):
        configs = GovernmentConnectorConfig.objects.filter(tenant=request.tenant).values()
        return Response(list(configs))
    def post(self, request):
        connector_type = request.data.get("connector_type",""); cfg, _ = GovernmentConnectorConfig.objects.update_or_create(
            tenant=request.tenant, connector_type=connector_type,
            defaults={"is_enabled":request.data.get("is_enabled",False),"api_endpoint":request.data.get("api_endpoint",""),
                      "api_key":request.data.get("api_key",""),"facility_id":request.data.get("facility_id","")},
        )
        return Response({"id":str(cfg.id),"connector_type":cfg.connector_type,"is_enabled":cfg.is_enabled}, status=201)


# Plugin Marketplace — Sprint B12

@extend_schema(tags=["marketplace"])
class PluginCatalogView(views.APIView):
    """Browse the plugin marketplace catalog."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "integrations.manage"

    def get(self, request):
        qs = Plugin.objects.filter(is_published=True)
        category = request.query_params.get("category")
        if category: qs = qs.filter(category=category)
        search = request.query_params.get("q")
        if search: qs = qs.filter(db_models.Q(name__icontains=search) | db_models.Q(description__icontains=search))
        return Response(list(qs.values(
            "id","name","slug","version","author","description","category","pricing_type","price",
            "is_certified","install_count","average_rating","icon_url",
        )))

@extend_schema(tags=["marketplace"])
class PluginInstallView(views.APIView):
    """Install/update plugin for this tenant."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "integrations.manage"

    def get(self, request):
        installed = PluginInstallation.objects.filter(tenant=request.tenant).select_related("plugin").values(
            "id","plugin__name","plugin__slug","installed_version","is_enabled","installed_at",
        )
        return Response(list(installed))

    def post(self, request):
        plugin_id = request.data.get("plugin_id")
        try: plugin = Plugin.objects.get(pk=plugin_id, is_published=True)
        except Plugin.DoesNotExist: return Response({"error":"Plugin not found"}, status=404)
        install, created = PluginInstallation.objects.get_or_create(
            tenant=request.tenant, plugin=plugin,
            defaults={"installed_version":plugin.version,"installed_by":request.user,"is_enabled":True},
        )
        if not created:
            install.is_enabled = request.data.get("is_enabled", True)
            install.installed_version = request.data.get("version", plugin.version)
            install.save()
        plugin.install_count = PluginInstallation.objects.filter(plugin=plugin).count()
        plugin.save(update_fields=["install_count"])
        return Response({"installed":str(install.id),"plugin":plugin.name,"is_enabled":install.is_enabled}, status=201)

    def delete(self, request):
        install_id = request.data.get("installation_id")
        try: install = PluginInstallation.objects.get(pk=install_id, tenant=request.tenant)
        except PluginInstallation.DoesNotExist: return Response({"error":"Not found"}, status=404)
        install.is_enabled = False; install.save(update_fields=["is_enabled"])
        return Response({"message":"Plugin disabled"})

@extend_schema(tags=["marketplace"])
class PluginReviewView(views.APIView):
    """Submit or view reviews for a plugin."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "integrations.manage"

    def get(self, request, plugin_pk):
        reviews = PluginReview.objects.filter(plugin_id=plugin_pk).select_related("reviewer").values(
            "id","rating","title","body","reviewer__first_name","reviewer__last_name","created_at",
        )
        return Response(list(reviews))

    def post(self, request, plugin_pk):
        review, created = PluginReview.objects.update_or_create(
            plugin_id=plugin_pk, tenant=request.tenant, reviewer=request.user,
            defaults={"rating":request.data.get("rating",5),"title":request.data.get("title",""),"body":request.data.get("body","")},
        )
        # Update average rating
        plugin = Plugin.objects.get(pk=plugin_pk)
        avg = PluginReview.objects.filter(plugin=plugin).aggregate(a=db_models.Avg("rating"))["a"] or 0
        plugin.average_rating = round(avg, 1); plugin.save(update_fields=["average_rating"])
        return Response({"id":str(review.id),"rating":review.rating}, status=201)

