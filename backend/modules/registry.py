"""
Module Registry — the central extension point for the platform.

Modules register capabilities (permissions, menu items, patient tabs,
dashboard widgets, reports, etc.) into this registry. The UI resolves
what to show based on the tenant's enabled modules and the user's role.

Full implementation in Sprint 7 (Dental Module).
"""


class ModuleRegistry:
    """
    Singleton registry that modules register their capabilities into.

    Capabilities a module can register:
        - permissions: list of (codename, description) tuples
        - appointment_types: list of type configs
        - patient_tabs: list of {label, icon, component, permission}
        - menu_items: list of {label, icon, path, permission, parent}
        - dashboard_widgets: list of widget definitions
        - reports: list of report definitions
        - form_schemas: dict of form_name -> JSON Schema
        - clinical_templates: dict of template_name -> template config
        - settings_sections: list of settings form configs
        - notification_templates: list of notification template configs
        - billing_item_types: list of billing item type configs
        - search_filters: list of search filter configs
    """

    _modules: dict[str, dict] = {}

    @classmethod
    def register(cls, module_name: str, **capabilities):
        """Register a module's capabilities."""
        cls._modules[module_name] = capabilities

    @classmethod
    def get_enabled_capabilities(cls, tenant, capability_type: str) -> list:
        """Return all registered capabilities of a given type for enabled modules."""
        # TODO Sprint 7: filter by tenant.enabled_modules
        results = []
        for name, caps in cls._modules.items():
            if capability_type in caps:
                results.extend(caps[capability_type])
        return results

    @classmethod
    def unregister(cls, module_name: str):
        """Remove a module from the registry."""
        cls._modules.pop(module_name, None)
