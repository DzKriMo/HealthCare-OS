"""Tenant onboarding wizard views — Sprint B17."""
from rest_framework import views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import OnboardingStep, DEFAULT_ONBOARDING_STEPS, Tenant


@extend_schema(tags=["tenancy"])
class OnboardingStatusView(views.APIView):
    """Get onboarding progress for the current tenant."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "identity.manage_tenant"

    def get(self, request):
        tenant = request.tenant
        steps = OnboardingStep.objects.filter(tenant=tenant).order_by("display_order")
        # Ensure all default steps exist
        existing_names = set(s.step_name for s in steps)
        for name, order, desc in DEFAULT_ONBOARDING_STEPS:
            if name not in existing_names:
                OnboardingStep.objects.create(tenant=tenant, step_name=name, display_order=order, notes=desc)
        steps = OnboardingStep.objects.filter(tenant=tenant).order_by("display_order")
        completed = steps.filter(is_completed=True).count()
        total = steps.count()
        return Response({
            "progress_pct": round(completed / total * 100) if total > 0 else 0,
            "completed": completed, "total": total,
            "steps": [{"name":s.step_name,"order":s.display_order,"done":s.is_completed,"notes":s.notes} for s in steps],
        })

    def post(self, request):
        """Mark an onboarding step as complete."""
        tenant = request.tenant
        step_name = request.data.get("step_name")
        try:
            step = OnboardingStep.objects.get(tenant=tenant, step_name=step_name)
        except OnboardingStep.DoesNotExist:
            return Response({"error":"Step not found"}, status=404)
        step.is_completed = True; step.completed_by = request.user
        from django.utils import timezone
        step.completed_at = timezone.now()
        step.save()
        return Response({"step":step.step_name,"completed":True})


@extend_schema(tags=["tenancy"])
class EditionConfigView(views.APIView):
    """Get available product editions."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "identity.manage_tenant"

    def get(self, request):
        from .models import ProductEdition
        editions = ProductEdition.objects.filter(is_active=True).values()
        return Response(list(editions))
