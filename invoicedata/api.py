from __future__ import annotations

from typing import Any, Dict, List

from django.db.models import Sum, Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invoicelist
from .serializers import InvoicelistSerializer


# PUBLIC_INTERFACE
class InvoiceGraphAPIView(APIView):
    """Returns aggregated invoice data for charts (overall year view)."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Invoices"],
        summary="Invoice graphs overview",
        description="Returns multiple series for monthly totals, per-issuer pie, and number of invoices per issuer.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "default": {"type": "array", "items": {"type": "number"}},
                    "pie_label": {"type": "array", "items": {"type": "string"}},
                    "pie_data": {"type": "array", "items": {"type": "number"}},
                    "noi_label": {"type": "array", "items": {"type": "string"}},
                    "noi_data": {"type": "array", "items": {"type": "number"}},
                },
            }
        },
    )
    def get(self, request, *args, **kwargs):
        a = Invoicelist.objects.filter(date__range=["2020-01-01", "2020-01-30"]).aggregate(Sum("amount"))["amount__sum"]
        b = Invoicelist.objects.filter(date__range=["2020-02-01", "2020-02-30"]).aggregate(Sum("amount"))["amount__sum"]
        c = Invoicelist.objects.filter(date__range=["2020-03-01", "2020-03-30"]).aggregate(Sum("amount"))["amount__sum"]
        d = Invoicelist.objects.filter(date__range=["2020-04-01", "2020-04-30"]).aggregate(Sum("amount"))["amount__sum"]
        e = Invoicelist.objects.filter(date__range=["2020-05-01", "2020-05-30"]).aggregate(Sum("amount"))["amount__sum"]
        f = Invoicelist.objects.filter(date__range=["2020-06-01", "2020-06-30"]).aggregate(Sum("amount"))["amount__sum"]
        g = Invoicelist.objects.filter(date__range=["2020-07-01", "2020-07-30"]).aggregate(Sum("amount"))["amount__sum"]
        h = Invoicelist.objects.filter(date__range=["2020-08-01", "2020-08-30"]).aggregate(Sum("amount"))["amount__sum"]
        i = Invoicelist.objects.filter(date__range=["2020-09-01", "2020-09-30"]).aggregate(Sum("amount"))["amount__sum"]
        j = Invoicelist.objects.filter(date__range=["2020-10-01", "2020-10-30"]).aggregate(Sum("amount"))["amount__sum"]
        k = Invoicelist.objects.filter(date__range=["2020-11-01", "2020-11-30"]).aggregate(Sum("amount"))["amount__sum"]
        l = Invoicelist.objects.filter(date__range=["2020-12-01", "2020-12-30"]).aggregate(Sum("amount"))["amount__sum"]

        default_item = [a, b, c, d, e, f, g, h, i, j, k, l]
        month = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        pie_chart = Invoicelist.objects.values("issuer").annotate(Sum("amount"))
        pie_label: List[str] = []
        pie_data: List[float] = []
        for row in pie_chart:
            pie_label.append(row["issuer"])
            pie_data.append(row["amount__sum"] or 0)

        noi = Invoicelist.objects.values("issuer").annotate(num=Count("issuer"))
        noi_label: List[str] = []
        noi_data: List[int] = []
        for row in noi:
            noi_label.append(row["issuer"])
            noi_data.append(row["num"] or 0)

        data = {
            "labels": month,
            "default": [x or 0 for x in default_item],
            "pie_label": pie_label,
            "pie_data": pie_data,
            "noi_label": noi_label,
            "noi_data": noi_data,
        }
        return Response(data)


# PUBLIC_INTERFACE
class InvoiceGraphMonthlyAPIView(APIView):
    """Returns monthly per-day or per-invoice totals, and issuer-wise monthly splits."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Invoices"],
        summary="Invoice graphs monthly",
        description="Returns monthly aggregates including daily totals and issuer-wise splits. Month is optional; defaults to January 2020-like ranges used in pages.",
        parameters=[
            OpenApiParameter(
                name="month",
                description="Month name or number (not strictly parsed; endpoint uses predefined ranges).",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: {"type": "object"}},
    )
    def get(self, request, *args, **kwargs):
        # Keep logic consistent with original class graphMonthly in views.py
        query1 = Invoicelist.objects.values("date").annotate(Sum("amount"))
        label = []
        data1 = []
        for row in query1:
            label.append(row["date"])
            data1.append(row["amount__sum"] or 0)

        def series(start: str, end: str):
            q = Invoicelist.objects.filter(date__range=[start, end]).values("issuer").annotate(Sum("amount"))
            labels: List[str] = []
            values: List[float] = []
            for r in q:
                labels.append(r["issuer"])
                values.append(r["amount__sum"] or 0)
            return labels, values

        jan_label, jan_data = series("2020-01-01", "2020-01-31")
        feb_label, feb_data = series("2020-02-01", "2020-02-29")
        mar_label, mar_data = series("2020-03-01", "2020-03-31")
        apr_label, apr_data = series("2020-04-01", "2020-04-30")
        may_label, may_data = series("2020-05-01", "2020-05-31")
        jun_label, jun_data = series("2020-06-01", "2020-06-30")
        jul_label, jul_data = series("2020-07-01", "2020-07-31")
        aug_label, aug_data = series("2020-08-01", "2020-08-31")
        sep_label, sep_data = series("2020-09-01", "2020-09-30")
        oct_label, oct_data = series("2020-10-01", "2020-10-31")
        nov_label, nov_data = series("2020-11-01", "2020-11-30")
        dec_label, dec_data = series("2020-12-01", "2020-12-31")

        return Response(
            {
                "labels": label,
                "data1": data1,
                "jan_data": jan_data,
                "jab_label": jan_label,  # maintain original key used by templates/JS
                "feb_data": feb_data,
                "feb_label": feb_label,
                "mar_data": mar_data,
                "mar_label": mar_label,
                "apr_data": apr_data,
                "apr_label": apr_label,
                "may_data": may_data,
                "may_label": may_label,
                "jun_data": jun_data,
                "jun_label": jun_label,
                "jul_data": jul_data,
                "jul_label": jul_label,
                "aug_data": aug_data,
                "aug_label": aug_label,
                "sep_data": sep_data,
                "sep_label": sep_label,
                "oct_data": oct_data,
                "oct_label": oct_label,
                "nov_data": nov_data,
                "nov_label": nov_label,
                "dec_data": dec_data,
                "dec_label": dec_label,
            }
        )
