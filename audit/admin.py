from django.contrib import admin
from .models import AuditRule, AuditRun, AuditCheck, AuditFinding, AuditAction


@admin.register(AuditRule)
class AuditRuleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "severity", "is_active", "created_at")
    list_filter = ("is_active", "severity", "created_at")
    search_fields = ("code", "name", "description")


@admin.register(AuditRun)
class AuditRunAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "triggered_by", "invoices_count", "total_checks", "total_findings", "total_failed", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "notes")


@admin.register(AuditCheck)
class AuditCheckAdmin(admin.ModelAdmin):
    list_display = ("id", "run", "rule", "invoice", "status", "created_at")
    list_filter = ("status", "rule__severity", "created_at")
    search_fields = ("rule__code", "invoice__issuer", "message")


@admin.register(AuditFinding)
class AuditFindingAdmin(admin.ModelAdmin):
    list_display = ("id", "rule", "invoice", "severity", "status", "assignee", "created_at")
    list_filter = ("status", "severity", "created_at")
    search_fields = ("title", "description", "rule__code", "invoice__issuer")


@admin.register(AuditAction)
class AuditActionAdmin(admin.ModelAdmin):
    list_display = ("id", "finding", "action_type", "performed_by", "performed_at")
    list_filter = ("action_type", "performed_at")
    search_fields = ("comment",)
