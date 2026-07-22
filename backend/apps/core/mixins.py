"""Shared DRF mixins for tenant-scoped ViewSets."""
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.core.permissions import (
    HasWorkspaceAccess,
    HasWorkspaceRole,
    IsAuthenticatedAndActive,
    TenantObjectPermission,
)


class TenantViewSetMixin:
    """
    Auto-scopes querysets to request.workspace and injects workspace on create.

    Use on every tenant-owned ViewSet:
      class TaskViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
          ...
    """

    permission_classes = [
        IsAuthenticatedAndActive,
        HasWorkspaceAccess,
        HasWorkspaceRole,
        TenantObjectPermission,
    ]

    def get_workspace(self):
        workspace = getattr(self.request, "workspace", None)
        if workspace is None:
            raise ValidationError(
                {"workspace": "X-Workspace-Id header is required."}
            )
        return workspace

    def get_queryset(self):
        qs = super().get_queryset()
        workspace = getattr(self.request, "workspace", None)
        if workspace is None:
            return qs.none()
        if hasattr(qs, "for_workspace"):
            return qs.for_workspace(workspace)
        return qs.filter(workspace=workspace)

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        membership = getattr(self.request, "workspace_membership", None)
        if membership is None:
            raise PermissionDenied("Workspace membership required.")
        serializer.save(workspace=workspace)

    def perform_update(self, serializer):
        # Prevent workspace reassignment
        serializer.save(workspace=self.get_workspace())
