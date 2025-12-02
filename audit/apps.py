from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Django application configuration for the audit app."""
    name = "audit"
    verbose_name = "Invoice Audit"
    # Keep primary keys consistent with existing migrations (which use AutoField)
    default_auto_field = "django.db.models.AutoField"
