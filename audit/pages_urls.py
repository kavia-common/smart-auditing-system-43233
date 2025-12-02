from __future__ import annotations

from django.urls import path

from audit.views import FindingsListView, RunsListView, RunDetailView

app_name = "audit_pages"

urlpatterns = [
    path("findings/", FindingsListView.as_view(), name="findings"),
    path("runs/", RunsListView.as_view(), name="runs"),
    path("runs/<uuid:id>/", RunDetailView.as_view(), name="run-detail"),
]
