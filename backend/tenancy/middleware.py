"""
Tenant middleware — resolves the current tenant from the request.

Resolution strategy:
    1. Subdomain: {slug}.healthcare-os.local
    2. Header: X-Tenant-Slug (for desktop/mobile API calls)
    3. Path prefix: /t/{slug}/... (fallback)
    4. JWT claim: tenant_id in the access token (for authenticated requests)

The resolved tenant is attached to request.tenant for downstream use.
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("healthcare_os.tenancy")


class TenantMiddleware(MiddlewareMixin):
    """
    Resolve tenant from request, attach to request.tenant.

    Tenant resolution order:
        1. Subdomain: {slug}.localhost → slug
        2. X-Tenant header (API clients)
        3. JWT claim (authenticated users — tenant_id)
        4. Path prefix (if none of the above)

    Unresolved tenants receive a 404 for tenant-scoped endpoints.
    Admin and schema endpoints bypass tenant resolution.
    """

    TENANT_HEADER = "HTTP_X_TENANT_SLUG"
    BYPASS_PATHS = [
        "/admin/",
        "/api/schema/",
        "/api/docs/",
        "/api/redoc/",
        "/api/auth/login/",
        "/api/auth/token/refresh/",
        "/api/auth/password-reset/",
        "/api/health/",
    ]

    def _resolve_from_subdomain(self, request) -> str | None:
        host = request.get_host().split(":")[0]
        if host in ("localhost", "127.0.0.1", "0.0.0.0"):
            return None
        parts = host.split(".")
        if len(parts) >= 2:
            # {slug}.domain.com → slug
            return parts[0] if parts[0] not in ("www", "api", "app") else None
        return None

    def _resolve_from_header(self, request) -> str | None:
        return request.META.get(self.TENANT_HEADER)

    def _resolve_from_jwt(self, request) -> str | None:
        """Extract tenant_id from JWT access token if authenticated."""
        if hasattr(request, "auth") and request.auth:
            return request.auth.get("tenant_slug")
        return None

    def _should_bypass(self, path: str) -> bool:
        return any(path.startswith(bp) for bp in self.BYPASS_PATHS)

    def process_request(self, request):
        """Resolve tenant and attach to request."""
        from tenancy.models import Tenant

        path = request.path

        if self._should_bypass(path):
            request.tenant = None
            return None

        # Try all resolution methods in order
        slug = (
            self._resolve_from_subdomain(request)
            or self._resolve_from_header(request)
            or self._resolve_from_jwt(request)
        )

        if slug:
            try:
                request.tenant = Tenant.objects.get(slug=slug, is_active=True)
            except Tenant.DoesNotExist:
                return JsonResponse(
                    {
                        "error": {
                            "type": "TenantNotFound",
                            "detail": f"Tenant '{slug}' not found or inactive.",
                        }
                    },
                    status=404,
                )
        else:
            # No tenant resolved — allow for super admin (cross-tenant) access
            # but tenant-scoped views will reject if required
            request.tenant = None

        return None
