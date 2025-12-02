"""major_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from rest_framework.authtoken.views import obtain_auth_token

# Simple CSRF endpoint to set csrftoken cookie and return it for Swagger clients
def csrf_token_view(request):
    token = request.META.get("CSRF_COOKIE")
    return JsonResponse({"csrftoken": token})

urlpatterns = [
    path('api/ping/', __import__('major_project.api_public', fromlist=['']).ping, name='api-ping'),
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),

    # OpenAPI schema and documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Convenience docs index
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='api-docs'),

    # Auth utilities for Swagger execution
    # - DRF Token auth creation endpoint
    path('api/auth/token/', obtain_auth_token, name='api-token-auth'),
    # - CSRF cookie endpoint (GET) for session-auth unsafe methods
    path('api/auth/csrf/', ensure_csrf_cookie(csrf_token_view), name='api-csrf'),

    # API endpoints for audit app
    path('api/audit/', include('audit.urls')),
    # Optional server-rendered pages for audit app
    path('audit/', include('audit.pages_urls')),
    # Existing app URLs
    path('', include('invoicedata.urls')),
]




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)