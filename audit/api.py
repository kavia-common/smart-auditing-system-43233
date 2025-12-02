from __future__ import annotations

from typing import Any, Dict, Optional

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from audit.models import AuditCheck, AuditFinding, AuditRule, AuditRun
from audit.serializers import (
    AuditCheckSerializer,
    AuditFindingSerializer,
    AuditRuleSerializer,
    AuditRunSerializer,
)
from audit.services import run_audit_for_invoice
from invoicedata.models import Invoicelist


class StaffWritePermission(permissions.BasePermission):
    """
    Permission that allows any authenticated user to read (SAFE_METHODS),
    but requires staff user for write operations.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return bool(request.user and request.user.is_staff)


class DefaultPagination(PageNumberPagination):
    """Default PageNumber pagination with moderate page size."""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# PUBLIC_INTERFACE
class AuditRuleListCreateView(generics.ListCreateAPIView):
    """
    List and create audit rules.

    GET: List rules with optional filters: ?is_active=true&severity=HIGH
    POST: Create a new rule (staff only). Sets created_by to request.user if provided.
    """
    serializer_class = AuditRuleSerializer
    pagination_class = DefaultPagination
    permission_classes = [StaffWritePermission]

    @extend_schema(
        tags=["Audit Rules"],
        summary="List audit rules",
        description="List all audit rules with optional filters by is_active and severity.",
        parameters=[
            OpenApiParameter(name="is_active", description="Filter by active state (true/false).", required=False, type=str),
            OpenApiParameter(name="severity", description="Filter by severity LOW|MEDIUM|HIGH|CRITICAL.", required=False, type=str),
            OpenApiParameter(name="page", description="Page number.", required=False, type=int),
            OpenApiParameter(name="page_size", description="Page size.", required=False, type=int),
        ],
        responses={200: AuditRuleSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Audit Rules"],
        summary="Create audit rule",
        request=AuditRuleSerializer,
        responses={201: AuditRuleSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        qs = AuditRule.objects.all().order_by("-created_at")
        is_active = self.request.query_params.get("is_active")
        severity = self.request.query_params.get("severity")
        if is_active is not None:
            if is_active.lower() in ("true", "1", "yes"):
                qs = qs.filter(is_active=True)
            elif is_active.lower() in ("false", "0", "no"):
                qs = qs.filter(is_active=False)
        if severity:
            qs = qs.filter(severity=str(severity).upper())
        return qs

    def perform_create(self, serializer):
        # Set created_by if available
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)


# PUBLIC_INTERFACE
class AuditRuleRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update an audit rule.

    GET: Retrieve a rule by ID.
    PUT/PATCH: Update rule fields (staff only).
    """
    serializer_class = AuditRuleSerializer
    queryset = AuditRule.objects.all().order_by("-created_at")
    permission_classes = [StaffWritePermission]

    @extend_schema(tags=["Audit Rules"], summary="Retrieve audit rule", responses={200: AuditRuleSerializer})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Audit Rules"], summary="Update audit rule", request=AuditRuleSerializer, responses={200: AuditRuleSerializer})
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["Audit Rules"], summary="Partially update audit rule", request=AuditRuleSerializer, responses={200: AuditRuleSerializer})
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


# PUBLIC_INTERFACE
class AuditRunListView(generics.ListAPIView):
    """
    List audit runs.

    Filters:
      - status: PENDING|RUNNING|COMPLETED|FAILED
      - triggered_by: user id
    """
    serializer_class = AuditRunSerializer
    pagination_class = DefaultPagination
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Audit Runs"],
        summary="List audit runs",
        parameters=[
            OpenApiParameter(name="status", description="Filter by status PENDING|RUNNING|COMPLETED|FAILED.", required=False, type=str),
            OpenApiParameter(name="triggered_by", description="Filter by user id.", required=False, type=int),
        ],
        responses={200: AuditRunSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = AuditRun.objects.all().order_by("-created_at")
        status_q = self.request.query_params.get("status")
        trig = self.request.query_params.get("triggered_by")
        if status_q:
            qs = qs.filter(status=status_q.upper())
        if trig:
            qs = qs.filter(triggered_by_id=trig)
        return qs


# PUBLIC_INTERFACE
class AuditRunDetailView(generics.RetrieveAPIView):
    """
    Retrieve an audit run by UUID.
    """
    serializer_class = AuditRunSerializer
    queryset = AuditRun.objects.all()
    lookup_field = "id"
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Audit Runs"], summary="Retrieve audit run", responses={200: AuditRunSerializer})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# PUBLIC_INTERFACE
class AuditCheckListView(generics.ListAPIView):
    """
    List audit checks with filters:
      - invoice: invoice id
      - rule: rule id
      - status: PASS|FAIL|SKIP|ERROR
    """
    serializer_class = AuditCheckSerializer
    pagination_class = DefaultPagination
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Audit Checks"],
        summary="List audit checks",
        parameters=[
            OpenApiParameter(name="invoice", description="Filter by invoice id.", required=False, type=int),
            OpenApiParameter(name="rule", description="Filter by rule id.", required=False, type=int),
            OpenApiParameter(name="status", description="PASS|FAIL|SKIP|ERROR", required=False, type=str),
        ],
        responses={200: AuditCheckSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = AuditCheck.objects.select_related("rule", "run").all().order_by("-created_at")
        invoice = self.request.query_params.get("invoice")
        rule = self.request.query_params.get("rule")
        status_q = self.request.query_params.get("status")
        if invoice:
            qs = qs.filter(invoice_id=invoice)
        if rule:
            qs = qs.filter(rule_id=rule)
        if status_q:
            qs = qs.filter(status=status_q.upper())
        return qs


# PUBLIC_INTERFACE
class AuditCheckDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single audit check by ID.
    """
    serializer_class = AuditCheckSerializer
    queryset = AuditCheck.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=["Audit Checks"], summary="Retrieve audit check", responses={200: AuditCheckSerializer})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# PUBLIC_INTERFACE
class AuditFindingListCreateView(generics.ListCreateAPIView):
    """
    List (and staff create) audit findings.

    GET filters:
      - invoice: invoice id
      - severity: LOW|MEDIUM|HIGH|CRITICAL
      - status: OPEN|SUPPRESSED|RESOLVED
      - rule: rule id
    """
    serializer_class = AuditFindingSerializer
    pagination_class = DefaultPagination
    permission_classes = [StaffWritePermission]

    @extend_schema(
        tags=["Audit Findings"],
        summary="List audit findings",
        parameters=[
            OpenApiParameter(name="invoice", description="Filter by invoice id.", required=False, type=int),
            OpenApiParameter(name="severity", description="LOW|MEDIUM|HIGH|CRITICAL", required=False, type=str),
            OpenApiParameter(name="status", description="OPEN|SUPPRESSED|RESOLVED", required=False, type=str),
            OpenApiParameter(name="rule", description="Filter by rule id.", required=False, type=int),
        ],
        responses={200: AuditFindingSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Audit Findings"], summary="Create audit finding (staff)", request=AuditFindingSerializer, responses={201: AuditFindingSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        qs = AuditFinding.objects.select_related("rule").all().order_by("-created_at")
        invoice = self.request.query_params.get("invoice")
        severity = self.request.query_params.get("severity")
        status_q = self.request.query_params.get("status")
        rule = self.request.query_params.get("rule")
        if invoice:
            qs = qs.filter(invoice_id=invoice)
        if severity:
            qs = qs.filter(severity=str(severity).upper())
        if status_q:
            qs = qs.filter(status=str(status_q).upper())
        if rule:
            qs = qs.filter(rule_id=rule)
        return qs


# PUBLIC_INTERFACE
class AuditFindingRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update an audit finding.

    GET: Anyone authenticated.
    PUT/PATCH: Staff-only (via StaffWritePermission).
    """
    serializer_class = AuditFindingSerializer
    queryset = AuditFinding.objects.all()
    permission_classes = [StaffWritePermission]

    @extend_schema(tags=["Audit Findings"], summary="Retrieve audit finding", responses={200: AuditFindingSerializer})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Audit Findings"], summary="Update audit finding", request=AuditFindingSerializer, responses={200: AuditFindingSerializer})
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["Audit Findings"], summary="Partially update audit finding", request=AuditFindingSerializer, responses={200: AuditFindingSerializer})
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


# PUBLIC_INTERFACE
class TriggerAuditRunAPIView(APIView):
    """
    Trigger an audit run for a given invoice ID.

    Request: POST /api/audit/trigger/<invoice_id>/
    Response: 201 Created with AuditRun payload.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Audit Runs"],
        summary="Trigger audit run for invoice",
        description="Execute all active rules against a specific invoice and create an AuditRun with results.",
        responses={201: OpenApiResponse(response=AuditRunSerializer, description="Run started and completed.")},
    )
    def post(self, request, invoice_id: int, format=None):
        invoice = get_object_or_404(Invoicelist, pk=invoice_id)
        run = run_audit_for_invoice(
            invoice,
            triggered_by=request.user,
            notes="Triggered via API",
            scope_filters={"invoice_id": invoice.id},
        )
        data = AuditRunSerializer(run).data
        return Response(data, status=status.HTTP_201_CREATED)
