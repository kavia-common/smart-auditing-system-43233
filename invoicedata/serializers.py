from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import Invoicelist


# PUBLIC_INTERFACE
class InvoicelistSerializer(serializers.ModelSerializer):
    """Serializer for the Invoicelist model used in API documentation and Try-it-out."""

    class Meta:
        model = Invoicelist
        fields = [
            "id",
            "issuer",
            "invoice_number",
            "date",
            "amount",
            "currency",
            "other",
            "date_posted",
            "author",
        ]
        read_only_fields = ["id", "date_posted", "author"]
