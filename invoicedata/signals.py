from django.db.models.signals import post_save
from django.dispatch import receiver

from invoicedata.models import Invoicelist
from audit.services import run_audit_for_invoice


@receiver(post_save, sender=Invoicelist)
def run_audit_on_invoice_save(sender, instance: Invoicelist, created: bool, **kwargs):
    """
    Trigger an audit run for an invoice whenever it is created or updated.

    Idempotency:
    - The audit runner ensures only one OPEN finding exists per (rule, invoice).
    - We create a fresh AuditRun per save event to keep an execution trail.

    Notes:
    - This runs synchronously; for high throughput systems, a background task/queue is recommended.
    """
    # We avoid passing a user; if needed, views can explicitly call the service with request.user
    run_audit_for_invoice(instance, triggered_by=None, notes="Triggered by post_save signal")
