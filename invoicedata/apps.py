from django.apps import AppConfig


class InvoicedataConfig(AppConfig):
    name = 'invoicedata'
    # Keep primary keys consistent with existing migrations (which use AutoField)
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        # Import signal handlers to connect post_save for Invoicelist
        # Avoid circular imports by importing inside ready().
        import invoicedata.signals  # noqa: F401
