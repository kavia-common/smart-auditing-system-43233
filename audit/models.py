from __future__ import annotations

import uuid
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TimeStampedModel(models.Model):
    """Abstract base model that adds created/updated timestamp fields."""
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the record was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the record was last updated.")

    class Meta:
        abstract = True


class AuditRule(TimeStampedModel):
    """
    Defines an audit rule that can be executed against an invoice.
    A rule contains metadata like code, description, severity and active state.
    """
    SEVERITY_LOW = "LOW"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_HIGH = "HIGH"
    SEVERITY_CRITICAL = "CRITICAL"
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, "Low"),
        (SEVERITY_MEDIUM, "Medium"),
        (SEVERITY_HIGH, "High"),
        (SEVERITY_CRITICAL, "Critical"),
    ]

    name = models.CharField(max_length=200, help_text="Human friendly name for the rule.")
    code = models.SlugField(max_length=64, unique=True, help_text="Unique code identifier for this rule.")
    description = models.TextField(blank=True, help_text="Detailed description of the rule.")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM)
    is_active = models.BooleanField(default=True, help_text="If disabled, rule will not be executed.")
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_rules_created"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active", "severity"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class AuditRun(TimeStampedModel):
    """
    Represents an execution session of one or more rules across one or more invoices.
    Used to group results (checks and findings).
    """
    STATUS_PENDING = "PENDING"
    STATUS_RUNNING = "RUNNING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    triggered_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_runs"
    )
    notes = models.TextField(blank=True, help_text="Optional notes about this run or its scope.")
    scope_filters = models.JSONField(
        default=dict, blank=True, help_text="JSON description of the filter/scope for the run."
    )
    invoices_count = models.PositiveIntegerField(default=0, help_text="Number of invoices included in the run.")
    total_checks = models.PositiveIntegerField(default=0)
    total_findings = models.PositiveIntegerField(default=0)
    total_failed = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AuditRun {self.id} ({self.status})"


class AuditCheck(TimeStampedModel):
    """
    Result of running a single rule against a specific invoice within an AuditRun.
    A check records pass/fail/skip/error along with an optional message/score.
    """
    STATUS_PASS = "PASS"
    STATUS_FAIL = "FAIL"
    STATUS_SKIP = "SKIP"
    STATUS_ERROR = "ERROR"
    STATUS_CHOICES = [
        (STATUS_PASS, "Pass"),
        (STATUS_FAIL, "Fail"),
        (STATUS_SKIP, "Skipped"),
        (STATUS_ERROR, "Error"),
    ]

    run = models.ForeignKey(AuditRun, on_delete=models.CASCADE, related_name="checks")
    rule = models.ForeignKey("AuditRule", on_delete=models.PROTECT, related_name="checks")
    # Link to existing invoice model from invoicedata app
    invoice = models.ForeignKey(
        "invoicedata.Invoicelist", on_delete=models.CASCADE, related_name="audit_checks"
    )
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_PASS)
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, help_text="Optional score or confidence."
    )
    message = models.TextField(blank=True, help_text="Additional information about this check result.")
    metadata = models.JSONField(default=dict, blank=True, help_text="Optional data produced by the check.")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["rule", "invoice"]),
        ]
        unique_together = ("run", "rule", "invoice")

    def __str__(self) -> str:
        return f"Check {self.rule.code} on invoice {self.invoice_id} [{self.status}]"


class AuditFinding(TimeStampedModel):
    """
    A concrete issue raised by a failing AuditCheck.
    Findings can be triaged and resolved via AuditAction.
    """
    STATUS_OPEN = "OPEN"
    STATUS_SUPPRESSED = "SUPPRESSED"
    STATUS_RESOLVED = "RESOLVED"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_SUPPRESSED, "Suppressed"),
        (STATUS_RESOLVED, "Resolved"),
    ]

    check = models.ForeignKey(AuditCheck, on_delete=models.CASCADE, related_name="findings")
    invoice = models.ForeignKey("invoicedata.Invoicelist", on_delete=models.CASCADE, related_name="audit_findings")
    rule = models.ForeignKey(AuditRule, on_delete=models.PROTECT, related_name="findings")
    title = models.CharField(max_length=255, help_text="Short summary of the finding.")
    description = models.TextField(blank=True, help_text="Detailed description of the problem.")
    severity = models.CharField(
        max_length=10, choices=AuditRule.SEVERITY_CHOICES, default=AuditRule.SEVERITY_MEDIUM
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_OPEN)
    discovered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    assignee = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_audit_findings"
    )
    metadata = models.JSONField(default=dict, blank=True, help_text="Arbitrary JSON payload with context for the finding.")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["severity"]),
        ]

    def __str__(self) -> str:
        return f"Finding {self.rule.code} on invoice {self.invoice_id} ({self.status})"


class AuditAction(TimeStampedModel):
    """
    Action taken on an AuditFinding such as commenting, changing status, assigning, or suppressing.
    Keeps an immutable history of finding lifecycle updates.
    """
    ACTION_COMMENT = "COMMENT"
    ACTION_STATUS_CHANGE = "STATUS_CHANGE"
    ACTION_ASSIGN = "ASSIGN"
    ACTION_SUPPRESS = "SUPPRESS"
    ACTION_OTHER = "OTHER"
    ACTION_CHOICES = [
        (ACTION_COMMENT, "Comment"),
        (ACTION_STATUS_CHANGE, "Status Change"),
        (ACTION_ASSIGN, "Assign"),
        (ACTION_SUPPRESS, "Suppress"),
        (ACTION_OTHER, "Other"),
    ]

    finding = models.ForeignKey(AuditFinding, on_delete=models.CASCADE, related_name="actions")
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, default=ACTION_COMMENT)
    performed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_actions")
    performed_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    old_value = models.CharField(max_length=255, blank=True)
    new_value = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-performed_at", "-created_at"]

    def __str__(self) -> str:
        return f"Action {self.action_type} on finding {self.finding_id}"
