from __future__ import annotations

from django.urls import path

from audit.api import (
    AuditCheckDetailView,
    AuditCheckListView,
    AuditFindingListCreateView,
    AuditFindingRetrieveUpdateView,
    AuditRuleListCreateView,
    AuditRuleRetrieveUpdateView,
    AuditRunDetailView,
    AuditRunListView,
    TriggerAuditRunAPIView,
)

app_name = "audit_api"

urlpatterns = [
    # Rules
    path("rules/", AuditRuleListCreateView.as_view(), name="rules-list-create"),
    path("rules/<int:pk>/", AuditRuleRetrieveUpdateView.as_view(), name="rules-detail-update"),
    # Runs
    path("runs/", AuditRunListView.as_view(), name="runs-list"),
    path("runs/<uuid:id>/", AuditRunDetailView.as_view(), name="runs-detail"),
    # Checks
    path("checks/", AuditCheckListView.as_view(), name="checks-list"),
    path("checks/<int:pk>/", AuditCheckDetailView.as_view(), name="checks-detail"),
    # Findings
    path("findings/", AuditFindingListCreateView.as_view(), name="findings-list-create"),
    path("findings/<int:pk>/", AuditFindingRetrieveUpdateView.as_view(), name="findings-detail-update"),
    # Trigger
    path("trigger/<int:invoice_id>/", TriggerAuditRunAPIView.as_view(), name="trigger-invoice-run"),
]
