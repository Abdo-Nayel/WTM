"""
Multi-tenant queryset managers.

Every tenant-scoped model inherits TenantManager so that:
  - .for_workspace(ws) always filters by workspace_id
  - accidental cross-tenant leaks are harder at the ORM layer
"""
from django.db import models


class TenantQuerySet(models.QuerySet):
    def for_workspace(self, workspace):
        if workspace is None:
            return self.none()
        workspace_id = workspace.pk if hasattr(workspace, "pk") else workspace
        return self.filter(workspace_id=workspace_id)

    def for_user_workspaces(self, user):
        """Restrict to workspaces the user belongs to (any role)."""
        if user is None or not user.is_authenticated:
            return self.none()
        from apps.workspaces.models import WorkspaceMembership

        workspace_ids = WorkspaceMembership.objects.filter(
            user=user, is_active=True
        ).values_list("workspace_id", flat=True)
        return self.filter(workspace_id__in=workspace_ids)


class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_workspace(self, workspace):
        return self.get_queryset().for_workspace(workspace)

    def for_user_workspaces(self, user):
        return self.get_queryset().for_user_workspaces(user)
