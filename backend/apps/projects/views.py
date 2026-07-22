from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.mixins import TenantViewSetMixin
from apps.projects.models import BoardColumn, Epic, Label, Project
from apps.projects.serializers import (
    BoardColumnSerializer,
    EpicSerializer,
    LabelSerializer,
    ProjectSerializer,
)
from apps.workspaces.models import WorkspaceRole


class ProjectViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.select_related("lead").prefetch_related("columns")
    search_fields = ("name", "key")
    filterset_fields = ("is_archived", "key")
    required_role = WorkspaceRole.VIEWER

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            self.required_role = WorkspaceRole.PROJECT_MANAGER
        else:
            self.required_role = WorkspaceRole.VIEWER
        return super().get_permissions()

    @action(detail=True, methods=["get"])
    def board(self, request, pk=None):
        """Return columns + tasks for Kanban board."""
        from apps.tasks.models import Task
        from apps.tasks.serializers import TaskListSerializer

        project = self.get_object()
        columns = project.columns.all().order_by("position")
        tasks = (
            Task.objects.for_workspace(request.workspace)
            .filter(project=project, parent__isnull=True)
            .select_related("assignee", "reporter", "column", "epic")
            .prefetch_related("labels")
        )
        return Response(
            {
                "project": ProjectSerializer(project, context={"request": request}).data,
                "columns": BoardColumnSerializer(columns, many=True).data,
                "tasks": TaskListSerializer(tasks, many=True).data,
            }
        )


class EpicViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    serializer_class = EpicSerializer
    queryset = Epic.objects.select_related("project")
    filterset_fields = ("project", "is_done")
    search_fields = ("name",)

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        project = serializer.validated_data["project"]
        if project.workspace_id != workspace.id:
            raise ValidationError({"project": "Project not in active workspace."})
        serializer.save(workspace=workspace)


class LabelViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
    filterset_fields = ("project",)
    search_fields = ("name",)

    def perform_create(self, serializer):
        serializer.save(workspace=self.get_workspace())


class BoardColumnViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    serializer_class = BoardColumnSerializer
    queryset = BoardColumn.objects.select_related("project")
    filterset_fields = ("project",)

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "reorder",
        ):
            self.required_role = WorkspaceRole.PROJECT_MANAGER
        else:
            self.required_role = WorkspaceRole.VIEWER
        return super().get_permissions()

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        project = serializer.validated_data["project"]
        if str(project.workspace_id) != str(workspace.id):
            raise ValidationError({"project": "Project not in active workspace."})
        # Auto position at end if not provided
        if serializer.validated_data.get("position") is None:
            last = (
                BoardColumn.objects.for_workspace(workspace)
                .filter(project=project)
                .order_by("-position")
                .first()
            )
            serializer.save(
                workspace=workspace,
                position=(last.position + 1) if last else 0,
            )
        else:
            serializer.save(workspace=workspace)

    def perform_destroy(self, instance):
        # Move tasks in this column back to backlog before delete
        instance.tasks.update(column=None, is_in_backlog=True)
        super().perform_destroy(instance)

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """
        Body: { "project_id": "...", "order": ["col-uuid-1", "col-uuid-2", ...] }
        """
        project_id = request.data.get("project_id")
        order = request.data.get("order") or []
        if not project_id or not isinstance(order, list):
            raise ValidationError({"detail": "project_id and order[] are required."})
        workspace = self.get_workspace()
        try:
            project = Project.objects.for_workspace(workspace).get(pk=project_id)
        except Project.DoesNotExist as exc:
            raise ValidationError({"project_id": "Not found."}) from exc

        cols = {
            str(c.id): c
            for c in BoardColumn.objects.for_workspace(workspace).filter(project=project)
        }
        with transaction.atomic():
            for idx, col_id in enumerate(order):
                col = cols.get(str(col_id))
                if col:
                    col.position = idx
                    col.save(update_fields=["position", "updated_at"])
        qs = BoardColumn.objects.for_workspace(workspace).filter(project=project)
        return Response(
            BoardColumnSerializer(qs, many=True).data,
            status=status.HTTP_200_OK,
        )
