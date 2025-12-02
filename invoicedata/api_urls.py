from __future__ import annotations

from django.urls import path

from .api import InvoiceGraphAPIView, InvoiceGraphMonthlyAPIView

app_name = "invoicedata_api"

urlpatterns = [
    path("graphs/", InvoiceGraphAPIView.as_view(), name="graphs"),
    path("graphs/monthly/", InvoiceGraphMonthlyAPIView.as_view(), name="graphs-monthly"),
]
