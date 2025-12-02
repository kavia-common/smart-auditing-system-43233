from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from audit.models import AuditAction, AuditCheck, AuditFinding, AuditRule, AuditRun
from invoicedata.models import Invoicelist


@dataclass
class RuleResult:
    """Container for the outcome of evaluating a rule against an invoice."""
    status: str  # "PASS" | "FAIL" | "SKIP" | "ERROR"
    message: str = ""
    metadata: Optional[Dict] = None


def _parse_blacklist_from_description(description: str) -> List[str]:
    """
    Parse vendor blacklist items from an AuditRule.description.
    We expect a comma-separated list of vendor names (case-insensitive matching).
    Example: "amazon, acme corp, foo ltd"
    """
    if not description:
        return []
    items = [x.strip() for x in description.split(",") if x.strip()]
    return items


def _evaluate_rule(rule: AuditRule, invoice: Invoicelist) -> RuleResult:
    """
    Evaluate a single rule by its code against the invoice.

    Supported minimal rules:
    - vendor_blacklist: If invoice.issuer matches a blacklisted vendor (comma separated in description), FAIL.
    - total_mismatch: Minimal variant: if invoice.amount is null, non-positive, or clearly invalid, FAIL.
                      In absence of line items, we treat non-positive amounts as mismatch.

    Any unknown rule code will be SKIP to remain forward-compatible.
    """
    code = (rule.code or "").strip().lower()
    try:
        if code == "vendor_blacklist":
            blacklist = _parse_blacklist_from_description(rule.description or "")
            if not blacklist:
                return RuleResult(status=AuditCheck.STATUS_SKIP, message="No blacklist configured on rule.")
            issuer = (invoice.issuer or "").strip().lower()
            for bad in blacklist:
                if issuer == bad.lower():
                    return RuleResult(
                        status=AuditCheck.STATUS_FAIL,
                        message=f"Issuer '{invoice.issuer}' is present in blacklist.",
                        metadata={"issuer": invoice.issuer, "blacklist": blacklist},
                    )
            return RuleResult(status=AuditCheck.STATUS_PASS, message="Issuer not blacklisted.")

        if code == "total_mismatch":
            # Minimal check only: ensure amount is a positive integer > 0
            try:
                amt = int(invoice.amount)
            except Exception:
                return RuleResult(
                    status=AuditCheck.STATUS_FAIL,
                    message="Invoice amount is not a valid integer.",
                    metadata={"raw_amount": invoice.amount},
                )
            if amt <= 0:
                return RuleResult(
                    status=AuditCheck.STATUS_FAIL,
                    message="Invoice amount must be greater than zero.",
                    metadata={"amount": amt},
                )
            return RuleResult(status=AuditCheck.STATUS_PASS, message="Amount appears valid (> 0).")

        # Unknown rules are skipped
        return RuleResult(status=AuditCheck.STATUS_SKIP, message=f"Unknown rule code: {rule.code!r}")
    except Exception as exc:
        return RuleResult(status=AuditCheck.STATUS_ERROR, message=f"Rule execution error: {exc!r}")


def _get_or_create_open_finding_for(rule: AuditRule, invoice: Invoicelist, check: AuditCheck) -> Tuple[AuditFinding, bool]:
    """
    Idempotently retrieve an OPEN finding for a given rule+invoice if it exists;
    otherwise create a new OPEN finding linked to the provided check.

    Returns (finding, created: bool).
    """
    existing = AuditFinding.objects.filter(
        rule=rule, invoice=invoice, status=AuditFinding.STATUS_OPEN
    ).order_by("-created_at").first()
    if existing:
        # Ensure this check is associated too (it may be a newer run)
        if existing.check_id != check.id:
            existing.check = check
            existing.save(update_fields=["check", "updated_at"])
        return existing, False

    finding = AuditFinding.objects.create(
        check=check,
        invoice=invoice,
        rule=rule,
        title=f"{rule.name} failed for invoice {invoice.pk}",
        description=check.message or f"Rule {rule.code} failed.",
        severity=rule.severity,
        status=AuditFinding.STATUS_OPEN,
        metadata=check.metadata or {},
    )
    return finding, True


# PUBLIC_INTERFACE
def run_audit_for_invoice(invoice: Invoicelist, triggered_by=None, notes: str = "", scope_filters: Optional[Dict] = None) -> AuditRun:
    """
    Run all active audit rules against a single invoice and persist results.

    - Creates an AuditRun to group the execution.
    - For each active AuditRule:
        - Evaluates the rule against the invoice.
        - Creates an AuditCheck result (PASS/FAIL/SKIP/ERROR).
        - If FAIL: ensure idempotent creation of an OPEN AuditFinding (one open finding per rule+invoice).
    - Updates run counters and returns the finalized AuditRun.

    Parameters:
        invoice: Invoicelist instance to evaluate.
        triggered_by: Optional User that initiated the run (can be None for system/signal).
        notes: Optional run-level notes.
        scope_filters: Optional JSON-like dict describing the scope; stored on the run.

    Returns:
        The completed AuditRun instance with counters updated.
    """
    active_rules = list(AuditRule.objects.filter(is_active=True).order_by("created_at"))
    scope = scope_filters or {"invoice_id": invoice.pk}

    with transaction.atomic():
        run = AuditRun.objects.create(
            status=AuditRun.STATUS_RUNNING,
            triggered_by=triggered_by,
            notes=notes,
            scope_filters=scope,
            invoices_count=1,
            started_at=timezone.now(),
        )

        total_checks = 0
        total_findings = 0
        total_failed = 0

        for rule in active_rules:
            result = _evaluate_rule(rule, invoice)
            check = AuditCheck.objects.create(
                run=run,
                rule=rule,
                invoice=invoice,
                status=result.status,
                message=result.message,
                metadata=result.metadata or {},
            )
            total_checks += 1

            if result.status == AuditCheck.STATUS_FAIL:
                total_failed += 1
                finding, created = _get_or_create_open_finding_for(rule, invoice, check)
                if created:
                    total_findings += 1

        run.total_checks = total_checks
        run.total_findings = total_findings
        run.total_failed = total_failed
        run.status = AuditRun.STATUS_COMPLETED
        run.ended_at = timezone.now()
        run.save(update_fields=[
            "total_checks", "total_findings", "total_failed",
            "status", "invoices_count", "ended_at", "updated_at"
        ])

    return run
