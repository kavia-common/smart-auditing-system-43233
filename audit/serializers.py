from __future__ import annotations

from typing import Any, Dict

from rest_framework import serializers

from audit.models import AuditAction, AuditCheck, AuditFinding, AuditRule, AuditRun


# PUBLIC_INTERFACE
class AuditRuleSerializer(serializers.ModelSerializer):
    """Serializer for AuditRule model; used for listing, creating, and updating rules."""

    created_by_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AuditRule
        fields = [
            "id",
            "created_at",
            "updated_at",
            "name",
            "code",
            "description",
            "severity",
            "is_active",
            "created_by",
            "created_by_username",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by_username"]

    def get_created_by_username(self, obj: AuditRule) -> str:
        return getattr(obj.created_by, "username", "") or ""


# PUBLIC_INTERFACE
class AuditRunSerializer(serializers.ModelSerializer):
    """Serializer for AuditRun model."""

    triggered_by_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AuditRun
        fields = [
            "id",
            "created_at",
            "updated_at",
            "status",
            "triggered_by",
            "triggered_by_username",
            "notes",
            "scope_filters",
            "invoices_count",
            "total_checks",
            "total_findings",
            "total_failed",
            "started_at",
            "ended_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "invoices_count",
            "total_checks",
            "total_findings",
            "total_failed",
            "started_at",
            "ended_at",
            "triggered_by_username",
        ]

    def get_triggered_by_username(self, obj: AuditRun) -> str:
        return getattr(obj.triggered_by, "username", "") or ""


# PUBLIC_INTERFACE
class AuditCheckSerializer(serializers.ModelSerializer):
    """Serializer for AuditCheck model."""

    rule_code = serializers.CharField(source="rule.code", read_only=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = AuditCheck
        fields = [
            "id",
            "created_at",
            "updated_at",
            "run",
            "rule",
            "rule_code",
            "rule_name",
            "invoice",
            "status",
            "score",
            "message",
            "metadata",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "rule_code", "rule_name"]


# PUBLIC_INTERFACE
class AuditFindingSerializer(serializers.ModelSerializer):
    """Serializer for AuditFinding model."""

    rule_code = serializers.CharField(source="rule.code", read_only=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = AuditFinding
        fields = [
            "id",
            "created_at",
            "updated_at",
            "audit_check",
            "invoice",
            "rule",
            "rule_code",
            "rule_name",
            "title",
            "description",
            "severity",
            "status",
            "discovered_at",
            "resolved_at",
            "assignee",
            "metadata",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "discovered_at", "rule_code", "rule_name"]


# PUBLIC_INTERFACE
class AuditActionSerializer(serializers.ModelSerializer):
    """Serializer for AuditAction model."""

    performed_by_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AuditAction
        fields = [
            "id",
            "created_at",
            "updated_at",
            "finding",
            "action_type",
            "performed_by",
            "performed_by_username",
            "performed_at",
            "comment",
            "old_value",
            "new_value",
            "metadata",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "performed_at", "performed_by_username"]

    def get_performed_by_username(self, obj: AuditAction) -> str:
        return getattr(obj.performed_by, "username", "") or ""
