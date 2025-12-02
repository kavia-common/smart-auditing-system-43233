from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from audit.models import AuditFinding, AuditRun


class FindingsListView(LoginRequiredMixin, ListView):
    """Simple template-based listing of audit findings with basic query filters."""
    model = AuditFinding
    template_name = "audit/findings_list.html"
    context_object_name = "findings"
    paginate_by = 20

    def get_queryset(self):
        qs = self.model.objects.select_related("rule").all().order_by("-created_at")
        invoice = self.request.GET.get("invoice")
        severity = self.request.GET.get("severity")
        status_q = self.request.GET.get("status")
        if invoice:
            qs = qs.filter(invoice_id=invoice)
        if severity:
            qs = qs.filter(severity=str(severity).upper())
        if status_q:
            qs = qs.filter(status=str(status_q).upper())
        return qs


class RunsListView(LoginRequiredMixin, ListView):
    """Template-based listing of audit runs."""
    model = AuditRun
    template_name = "audit/runs_list.html"
    context_object_name = "runs"
    paginate_by = 20

    def get_queryset(self):
        qs = self.model.objects.all().order_by("-created_at")
        status_q = self.request.GET.get("status")
        if status_q:
            qs = qs.filter(status=str(status_q).upper())
        return qs


class RunDetailView(LoginRequiredMixin, DetailView):
    """Detail page for a single audit run."""
    model = AuditRun
    template_name = "audit/run_detail.html"
    context_object_name = "run"
    pk_url_kwarg = "id"
