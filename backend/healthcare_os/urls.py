"""
Healthcare OS URL Configuration.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from .views import health_check, metrics

urlpatterns = [
    # Health check + metrics
    path("api/health/", health_check, name="health-check"),
    path("api/metrics/", metrics, name="metrics"),

    # Admin
    path("admin/", admin.site.urls),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # Auth
    path("api/auth/", include("identity.urls")),

    # Core domains
    path("api/", include("tenancy.urls")),
    path("api/patients/", include("patients.urls")),
    path("api/appointments/", include("scheduling.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/reports/", include("reporting.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/modules/", include("modules.urls")),
    path("api/dental/", include("modules.dental.urls")),
    path("api/integrations/", include("integrations.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/pharmacy/", include("pharmacy.urls")),
    path("api/lab/", include("laboratory.urls")),
    path("api/imaging/", include("imaging.urls")),
    path("api/clinical/", include("clinical.urls")),
    path("api/derm/", include("dermatology.urls")),
    path("api/ophth/", include("ophthalmology.urls")),
    path("api/cardio/", include("cardiology.urls")),
    path("api/peds/", include("pediatrics.urls")),
    path("api/gyn/", include("gynecology.urls")),
    path("api/ortho/", include("orthopedics.urls")),
    path("api/ent/", include("ent.urls")),
    path("api/physio/", include("physiotherapy.urls")),
    path("api/dialysis/", include("dialysis.urls")),
    path("api/onc/", include("oncology.urls")),
    path("api/er/", include("emergency.urls")),
    path("api/vet/", include("veterinary.urls")),
    path("fhir/", include("fhir.urls")),
    path("api/sync/", include("sync.urls")),
    path("api/telemedicine/", include("telemedicine.urls")),
    path("api/ai/", include("ai_diagnostics.urls")),
    path("api/bots/", include("bots.urls")),
]
