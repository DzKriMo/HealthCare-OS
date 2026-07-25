from django.urls import path
from . import onboarding_views

app_name = "tenancy"

urlpatterns = [
    path("onboarding/", onboarding_views.OnboardingStatusView.as_view(), name="onboarding"),
    path("editions/", onboarding_views.EditionConfigView.as_view(), name="editions"),
]
