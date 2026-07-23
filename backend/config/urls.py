from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404, JsonResponse
from django.urls import include, path, re_path
from django.views.decorators.cache import never_cache
from django.views.static import serve as media_serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.auth import WorkTaskMeTokenObtainPairView
from apps.accounts.views import CheckEmailView, MeOverviewView
from apps.core.notification_views import NotificationViewSet

# WorkTaskMe / WTM admin branding
admin.site.site_header = "WorkTaskMe Admin"
admin.site.site_title = "WTM Portal"
admin.site.index_title = "WorkTaskMe Workspace Management"

WEB_DIR_CANDIDATES = [
    Path(__file__).resolve().parent.parent.parent / "web",
    Path("/web"),
    Path(__file__).resolve().parent.parent / "web",
]

WEB_CANDIDATES = [d / "index.html" for d in WEB_DIR_CANDIDATES]

notif_router = DefaultRouter()
notif_router.register(r"notifications", NotificationViewSet, basename="notification")


def health(_request):
    return JsonResponse({"status": "ok", "service": "worktaskme"})


@never_cache
def spa(_request):
    for candidate in WEB_CANDIDATES:
        if candidate.exists():
            response = FileResponse(
                candidate.open("rb"), content_type="text/html; charset=utf-8"
            )
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            return response
    return JsonResponse(
        {"detail": "Web UI missing. Open /api/docs/ for the API."},
        status=404,
    )


def web_assets(request, path):
    """Serve logo / static files from the sibling web/ directory."""
    # Prevent path traversal
    safe = Path(path)
    if ".." in safe.parts:
        raise Http404()
    for root in WEB_DIR_CANDIDATES:
        candidate = (root / "assets" / safe).resolve()
        try:
            candidate.relative_to((root / "assets").resolve())
        except ValueError:
            continue
        if candidate.is_file():
            return media_serve(request, str(safe).replace("\\", "/"), document_root=str(root / "assets"))
    raise Http404()


urlpatterns = [
    path("", spa, name="spa"),
    path("reset-password/", spa, name="spa-reset-password"),
    path("reset-password", spa, name="spa-reset-password-noslash"),
    re_path(r"^assets/(?P<path>.*)$", web_assets, name="web-assets"),
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/token/", WorkTaskMeTokenObtainPairView.as_view(), name="token_obtain"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/check-email/", CheckEmailView.as_view(), name="auth-check-email"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/me/overview/", MeOverviewView.as_view(), name="me-overview"),
    path("api/workspaces/", include("apps.workspaces.urls")),
    path("api/projects/", include("apps.projects.urls")),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/calendar/", include("apps.calendar_events.urls")),
    path("api/", include(notif_router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# Serve uploaded media (attachments / images). django.conf.urls.static only
# registers when DEBUG=True — keep an explicit route so local Daphne works too.
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        media_serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
