from channels.layers import get_channel_layer
from django.conf import settings
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.consumers import broadcast_workspace_event
from apps.core.mixins import TenantViewSetMixin
from apps.tasks.models import Task, TaskActivity, TaskAttachment
from apps.tasks.serializers import (
    TaskActivitySerializer,
    TaskAttachmentSerializer,
    TaskCommentSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskMoveSerializer,
)


class TaskFilter(filters.FilterSet):
    project = filters.UUIDFilter(field_name="project_id")
    column = filters.UUIDFilter(field_name="column_id")
    epic = filters.UUIDFilter(field_name="epic_id")
    assignee = filters.UUIDFilter(field_name="assignee_id")
    priority = filters.CharFilter()
    task_type = filters.CharFilter()
    is_in_backlog = filters.BooleanFilter()
    due_before = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    due_after = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Task
        fields = [
            "project",
            "column",
            "epic",
            "assignee",
            "priority",
            "task_type",
            "is_in_backlog",
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(title__icontains=value) | queryset.filter(
            issue_key__icontains=value
        )


class TaskViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = Task.objects.select_related(
        "assignee", "reporter", "project", "column", "epic", "parent"
    ).prefetch_related("labels", "subtasks", "attachments")
    filterset_class = TaskFilter
    search_fields = ("title", "issue_key", "description")
    ordering_fields = (
        "board_position",
        "priority",
        "due_date",
        "story_points",
        "created_at",
        "updated_at",
    )

    def get_serializer_class(self):
        if self.action == "list":
            return TaskListSerializer
        if self.action == "move":
            return TaskMoveSerializer
        return TaskDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Board lists: top-level only unless explicitly requested
        if self.action == "list" and self.request.query_params.get("include_subtasks") != "1":
            qs = qs.filter(parent__isnull=True)
        return qs

    def perform_create(self, serializer):
        # TaskDetailSerializer.create already sets workspace
        serializer.save()
        task = serializer.instance
        self._broadcast("task.created", task)
        TaskActivity.objects.create(
            workspace=task.workspace,
            task=task,
            actor=self.request.user,
            action="created",
            meta={"issue_key": task.issue_key},
        )

    def perform_update(self, serializer):
        before_column = serializer.instance.column_id
        # Keep workspace immutable; do not pass it into field assignment
        serializer.save()
        task = serializer.instance
        self._broadcast("task.updated", task)
        if before_column != task.column_id:
            try:
                TaskActivity.objects.create(
                    workspace=task.workspace,
                    task=task,
                    actor=self.request.user,
                    action="column_changed",
                    meta={"from": str(before_column), "to": str(task.column_id)},
                )
            except Exception:
                pass

    def perform_destroy(self, instance):
        self._broadcast("task.deleted", instance)
        super().perform_destroy(instance)

    def _broadcast(self, event_type, task):
        try:
            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            broadcast_workspace_event(
                channel_layer,
                "board",
                task.workspace_id,
                event_type,
                {
                    "id": str(task.id),
                    "issue_key": task.issue_key,
                    "column_id": str(task.column_id) if task.column_id else None,
                    "board_position": task.board_position,
                    "title": task.title,
                },
            )
        except Exception:
            # Realtime is best-effort; never break the API write path
            pass

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        """Kanban drag-and-drop endpoint."""
        task = self.get_object()
        serializer = TaskMoveSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        TaskActivity.objects.create(
            workspace=task.workspace,
            task=task,
            actor=request.user,
            action="moved",
            meta=serializer.validated_data,
        )
        self._broadcast("task.moved", task)
        return Response(TaskListSerializer(task).data)

    @action(detail=False, methods=["get"])
    def backlog(self, request):
        qs = self.filter_queryset(self.get_queryset().filter(is_in_backlog=True))
        page = self.paginate_queryset(qs)
        ser = TaskListSerializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            qs = task.comments.select_related("author")
            return Response(TaskCommentSerializer(qs, many=True).data)
        ser = TaskCommentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(
            workspace=task.workspace,
            task=task,
            author=request.user,
        )
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def activity(self, request, pk=None):
        task = self.get_object()
        qs = task.activities.select_related("actor")[:100]
        return Response(TaskActivitySerializer(qs, many=True).data)

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="attachments",
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    def attachments(self, request, pk=None):
        """
        GET  list attachments
        POST multipart: file=..., kind?=file|image|audio|video
        """
        task = self.get_object()
        if request.method == "GET":
            qs = task.attachments.select_related("uploaded_by")
            return Response(
                TaskAttachmentSerializer(qs, many=True, context={"request": request}).data
            )

        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "file is required"}, status=400)

        content_type = getattr(upload, "content_type", "") or ""
        kind = request.data.get("kind") or ""
        valid_kinds = {c.value for c in TaskAttachment.Kind}
        if kind not in valid_kinds:
            if content_type.startswith("image/"):
                kind = TaskAttachment.Kind.IMAGE
            elif content_type.startswith("audio/"):
                kind = TaskAttachment.Kind.AUDIO
            elif content_type.startswith("video/"):
                kind = TaskAttachment.Kind.VIDEO
            else:
                kind = TaskAttachment.Kind.FILE

        try:
            from pathlib import Path

            Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
            att = TaskAttachment.objects.create(
                workspace=task.workspace,
                task=task,
                uploaded_by=request.user,
                file=upload,
                kind=kind,
                original_name=(getattr(upload, "name", "") or "upload")[:255],
                content_type=content_type[:128],
                size_bytes=getattr(upload, "size", 0) or 0,
            )
        except Exception as exc:  # pragma: no cover
            return Response(
                {"detail": f"Upload failed: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            TaskAttachmentSerializer(att, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"attachments/(?P<attachment_id>[^/.]+)",
    )
    def delete_attachment(self, request, pk=None, attachment_id=None):
        task = self.get_object()
        try:
            att = task.attachments.get(pk=attachment_id)
        except TaskAttachment.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        if att.file:
            att.file.delete(save=False)
        att.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
