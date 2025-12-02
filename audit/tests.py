from django.contrib.auth import get_user_model
from django.test import TestCase

from audit.models import AuditFinding, AuditRule
from invoicedata.models import Invoicelist

User = get_user_model()


class AuditSignalTests(TestCase):
    def setUp(self) -> None:
        # Create a user to own invoices (model requires author)
        self.user = User.objects.create_user(username="tester", password="pass")

        # Minimal rules
        AuditRule.objects.create(
            name="Vendor Blacklist",
            code="vendor_blacklist",
            description="amazon, bad vendor inc",
            severity="HIGH",
            is_active=True,
            created_by=None,
        )
        AuditRule.objects.create(
            name="Total Mismatch",
            code="total_mismatch",
            description="Amount must be > 0",
            severity="MEDIUM",
            is_active=True,
            created_by=None,
        )

    def test_blacklisted_vendor_creates_finding(self):
        invoice = Invoicelist.objects.create(
            issuer="Amazon",
            invoice_number="INV-1",
            date="2020-01-20",
            amount=100,
            currency="USD",
            other="",
            author=self.user,
        )
        # post_save signal should have run and created findings for vendor blacklist (one open finding)
        findings = AuditFinding.objects.filter(invoice=invoice, rule__code="vendor_blacklist")
        self.assertEqual(findings.count(), 1)
        self.assertEqual(findings.first().status, "OPEN")

        # Save again should not create a duplicate OPEN finding for the same rule+invoice
        invoice.amount = 150
        invoice.save()
        findings = AuditFinding.objects.filter(invoice=invoice, rule__code="vendor_blacklist", status="OPEN")
        self.assertEqual(findings.count(), 1)

    def test_total_mismatch_on_non_positive_amount(self):
        invoice = Invoicelist.objects.create(
            issuer="OK Vendor",
            invoice_number="INV-2",
            date="2020-01-21",
            amount=0,  # non-positive triggers mismatch
            currency="USD",
            other="",
            author=self.user,
        )
        findings = AuditFinding.objects.filter(invoice=invoice, rule__code="total_mismatch")
        self.assertEqual(findings.count(), 1)
        self.assertIn("greater than zero", findings.first().description)
