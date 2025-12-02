from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# PUBLIC_INTERFACE
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def ping(request):
    """Simple public health ping endpoint for docs and uptime checks."""
    return Response({"status": "ok"})
