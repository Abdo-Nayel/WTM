"""
Workspace tenant middleware + locale resolution.

Reads `X-Workspace-Id` header and attaches:
  - request.workspace
  - request.workspace_membership

LocaleMiddleware sets request.LANGUAGE_CODE from ?lang= or Accept-Language.
"""
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from apps.core.i18n import normalize_lang, t


# Paths that do not require a workspace context
WORKSPACE_OPTIONAL_PREFIXES = (
    "/admin/",
    "/api/auth/",
    "/api/health/",
    "/api/schema/",
    "/api/docs/",
    "/api/workspaces/",  # listing / creating workspaces
    "/api/me/",
    "/static/",
    "/media/",
)


class LocaleMiddleware(MiddlewareMixin):
    """Resolve API language from ?lang=ar|en or Accept-Language."""

    def process_request(self, request):
        lang_param = request.GET.get("lang")
        if lang_param in ("ar", "en"):
            request.LANGUAGE_CODE = lang_param
            return None
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        request.LANGUAGE_CODE = normalize_lang(accept) if accept else "en"
        return None


class WorkspaceTenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.workspace = None
        request.workspace_membership = None

        path = request.path
        if any(path.startswith(p) for p in WORKSPACE_OPTIONAL_PREFIXES):
            # Still resolve header if present (useful for nested workspace routes)
            self._resolve_workspace(request, required=False)
            return None

        # All other /api/* routes require an authenticated user + workspace header
        if path.startswith("/api/"):
            return self._resolve_workspace(request, required=True)

        return None

    def _resolve_workspace(self, request, required: bool):
        header_name = getattr(settings, "WORKSPACE_HEADER", "HTTP_X_WORKSPACE_ID")
        raw_id = request.META.get(header_name) or request.headers.get("X-Workspace-Id")
        lang = getattr(request, "LANGUAGE_CODE", None)

        if not raw_id:
            if required:
                return JsonResponse(
                    {
                        "detail": t("workspace_required", lang=lang),
                        "code": "workspace_required",
                    },
                    status=400,
                )
            return None

        # Lazy imports to avoid AppRegistryNotReady
        from apps.workspaces.models import Workspace, WorkspaceMembership

        try:
            workspace = Workspace.objects.get(pk=raw_id, is_active=True)
        except (Workspace.DoesNotExist, ValueError):
            return JsonResponse(
                {
                    "detail": t("workspace_not_found", lang=lang),
                    "code": "workspace_not_found",
                },
                status=404,
            )

        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            # Auth middleware may run after us for session; JWT auth runs in DRF.
            # Store workspace; DRF permission will re-check membership.
            request.workspace = workspace
            return None

        membership = (
            WorkspaceMembership.objects.select_related("workspace")
            .filter(workspace=workspace, user=user, is_active=True)
            .first()
        )
        if membership is None:
            return JsonResponse(
                {
                    "detail": t("workspace_forbidden", lang=lang),
                    "code": "workspace_forbidden",
                },
                status=403,
            )

        request.workspace = workspace
        request.workspace_membership = membership
        return None
