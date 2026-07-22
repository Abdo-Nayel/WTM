"""
RBAC + workspace-scoped DRF permissions.

Roles (highest → lowest privilege):
  admin > project_manager > member > viewer
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.workspaces.models import WorkspaceRole


ROLE_RANK = {
    WorkspaceRole.VIEWER: 1,
    WorkspaceRole.MEMBER: 2,
    WorkspaceRole.PROJECT_MANAGER: 3,
    WorkspaceRole.ADMIN: 4,
}


def _membership(request):
    membership = getattr(request, "workspace_membership", None)
    if membership is not None:
        return membership

    workspace = getattr(request, "workspace", None)
    user = getattr(request, "user", None)
    if workspace is None or user is None or not user.is_authenticated:
        return None

    from apps.workspaces.models import WorkspaceMembership

    membership = (
        WorkspaceMembership.objects.filter(
            workspace=workspace, user=user, is_active=True
        ).first()
    )
    request.workspace_membership = membership
    return membership


def has_min_role(membership, min_role: str) -> bool:
    if membership is None:
        return False
    return ROLE_RANK.get(membership.role, 0) >= ROLE_RANK.get(min_role, 99)


class IsAuthenticatedAndActive(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_active", True)
        )


class HasWorkspaceAccess(BasePermission):
    """User must be an active member of request.workspace."""

    message = "Workspace membership required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        workspace = getattr(request, "workspace", None)
        if workspace is None:
            # Allow views that resolve workspace from URL kwargs
            return True
        return _membership(request) is not None


class HasWorkspaceRole(BasePermission):
    """
    Enforce a minimum role.

    Set on the view:
      required_role = WorkspaceRole.MEMBER
    Defaults to MEMBER for writes, VIEWER for reads.
    """

    message = "Insufficient workspace role."

    def has_permission(self, request, view):
        membership = _membership(request)
        if membership is None:
            # If no workspace on request, defer to object-level / view logic
            if getattr(request, "workspace", None) is None:
                return True
            return False

        required = getattr(view, "required_role", None)
        if required is None:
            required = (
                WorkspaceRole.VIEWER
                if request.method in SAFE_METHODS
                else WorkspaceRole.MEMBER
            )
        return has_min_role(membership, required)


class IsWorkspaceAdmin(BasePermission):
    message = "Workspace admin role required."

    def has_permission(self, request, view):
        return has_min_role(_membership(request), WorkspaceRole.ADMIN)


class IsProjectManagerOrAbove(BasePermission):
    message = "Project manager role or higher required."

    def has_permission(self, request, view):
        return has_min_role(_membership(request), WorkspaceRole.PROJECT_MANAGER)


class TenantObjectPermission(BasePermission):
    """Object must belong to the active workspace."""

    message = "Object does not belong to the active workspace."

    def has_object_permission(self, request, view, obj):
        workspace = getattr(request, "workspace", None)
        if workspace is None:
            return False
        obj_ws = getattr(obj, "workspace_id", None)
        if obj_ws is None and hasattr(obj, "workspace"):
            obj_ws = getattr(obj.workspace, "pk", None)
        return str(obj_ws) == str(workspace.pk)
