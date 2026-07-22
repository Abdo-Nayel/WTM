import re

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.core.i18n import t
from apps.projects.serializers import LabelSerializer
from apps.tasks.models import Task, TaskActivity, TaskAttachment, TaskComment

# Images must be TaskAttachments — never store base64 or markdown image embeds in description.
_DATA_URI_RE = re.compile(
    r"!?\[[^\]]*\]\(data:image\/[^)]+\)|data:image\/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\s]+",
    re.IGNORECASE,
)
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_MAX_DESCRIPTION_LEN = 50_000


class TaskCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ("id", "task", "author", "body", "created_at", "updated_at")
        read_only_fields = ("id", "task", "author", "created_at", "updated_at")


class TaskAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = TaskAttachment
        fields = (
            "id",
            "task",
            "kind",
            "original_name",
            "content_type",
            "size_bytes",
            "url",
            "uploaded_by",
            "created_at",
        )
        read_only_fields = fields

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        url = obj.file.url or ""
        # Ensure absolute path so build_absolute_uri never resolves relative to /api/...
        if url and not url.startswith(("http://", "https://", "/")):
            url = f"/{url}"
        if request:
            return request.build_absolute_uri(url)
        return url


class TaskActivitySerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = TaskActivity
        fields = ("id", "task", "actor", "action", "meta", "created_at")
        read_only_fields = fields


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for boards / backlog lists."""

    assignee = UserSerializer(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    subtask_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "epic",
            "parent",
            "column",
            "issue_key",
            "title",
            "task_type",
            "priority",
            "story_points",
            "board_position",
            "is_in_backlog",
            "assignee",
            "labels",
            "due_date",
            "start_date",
            "subtask_count",
            "updated_at",
        )

    def get_subtask_count(self, obj):
        if hasattr(obj, "_subtask_count"):
            return obj._subtask_count
        return obj.subtasks.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    reporter = UserSerializer(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    subtasks = TaskListSerializer(many=True, read_only=True)

    assignee_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )
    column_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    epic_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    label_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    project_id = serializers.UUIDField(write_only=True, required=False)
    # Explicit writable field so PATCH always accepts backlog toggles
    is_in_backlog = serializers.BooleanField(required=False)

    class Meta:
        model = Task
        fields = (
            "id",
            "project",
            "project_id",
            "epic",
            "epic_id",
            "parent",
            "parent_id",
            "column",
            "column_id",
            "issue_number",
            "issue_key",
            "title",
            "description",
            "task_type",
            "priority",
            "story_points",
            "board_position",
            "is_in_backlog",
            "reporter",
            "assignee",
            "assignee_id",
            "labels",
            "label_ids",
            "due_date",
            "start_date",
            "estimated_hours",
            "comments",
            "attachments",
            "subtasks",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "project",
            "epic",
            "parent",
            "column",
            "issue_number",
            "issue_key",
            "reporter",
            "assignee",
            "labels",
            "comments",
            "attachments",
            "subtasks",
            "created_at",
            "updated_at",
        )

    def validate_description(self, value):
        text = value or ""
        # Strip embedded images (markdown + data-URI). Files belong in TaskAttachment.
        cleaned = _MD_IMG_RE.sub("", text)
        cleaned = _DATA_URI_RE.sub("", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        if len(cleaned) > _MAX_DESCRIPTION_LEN:
            raise serializers.ValidationError(
                "Description is too long. Upload images as attachments instead of embedding them."
            )
        return cleaned

    def validate_assignee_id(self, value):
        if value in ("", None):
            return None
        return value

    def validate_column_id(self, value):
        if value in ("", None):
            return None
        return value

    def validate_story_points(self, value):
        if value in ("", None):
            return None
        try:
            n = int(value)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError("Enter a whole number.") from exc
        if n < 0 or n > 1000:
            raise serializers.ValidationError("Story points must be between 0 and 1000.")
        return n

    def validate_due_date(self, value):
        if value in ("", None):
            return None
        return value

    def to_internal_value(self, data):
        # Accept mutable copies; coerce blank strings for nullable fields
        if hasattr(data, "copy"):
            data = data.copy()
        else:
            data = dict(data)
        for key in ("assignee_id", "column_id", "epic_id", "parent_id", "due_date", "start_date"):
            if key in data and data[key] == "":
                data[key] = None
        if "story_points" in data and data["story_points"] == "":
            data["story_points"] = None
        return super().to_internal_value(data)

    def create(self, validated_data):
        from apps.projects.models import Project

        request = self.context.get("request")
        label_ids = validated_data.pop("label_ids", None)
        project_id = validated_data.pop("project_id", None)
        if not project_id:
            raise serializers.ValidationError(
                {"project_id": t("project_id_required", request=request)}
            )
        assignee_id = validated_data.pop("assignee_id", None)
        column_id = validated_data.pop("column_id", None)
        epic_id = validated_data.pop("epic_id", None)
        parent_id = validated_data.pop("parent_id", None)

        workspace = self.context["request"].workspace
        try:
            project = Project.objects.for_workspace(workspace).get(pk=project_id)
        except Project.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"project_id": t("project_not_found", request=request)}
            ) from exc

        if validated_data.get("task_type") == "subtask" and not parent_id:
            raise serializers.ValidationError(
                {"parent_id": t("subtask_needs_parent", request=request)}
            )

        task = Task.create_with_key(
            project=project,
            workspace=workspace,
            reporter=self.context["request"].user,
            assignee_id=assignee_id,
            column_id=column_id,
            epic_id=epic_id,
            parent_id=parent_id,
            **validated_data,
        )
        if label_ids is not None:
            from apps.projects.models import Label

            task.labels.set(
                Label.objects.for_workspace(workspace).filter(pk__in=label_ids)
            )
        return task

    def update(self, instance, validated_data):
        from apps.projects.models import Label

        validated_data.pop("project_id", None)  # immutable
        # workspace may be injected via serializer.save(workspace=...); keep current
        validated_data.pop("workspace", None)
        label_ids = validated_data.pop("label_ids", None)

        if "column_id" in validated_data:
            instance.column_id = validated_data.pop("column_id")
            if instance.column_id is not None and "is_in_backlog" not in validated_data:
                instance.is_in_backlog = False

        if "assignee_id" in validated_data:
            instance.assignee_id = validated_data.pop("assignee_id")
        if "epic_id" in validated_data:
            instance.epic_id = validated_data.pop("epic_id")
        if "parent_id" in validated_data:
            instance.parent_id = validated_data.pop("parent_id")

        if "is_in_backlog" in validated_data:
            instance.is_in_backlog = validated_data.pop("is_in_backlog")
            if instance.is_in_backlog and "column_id" not in self.initial_data:
                instance.column_id = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if label_ids is not None:
            instance.labels.set(
                Label.objects.for_workspace(instance.workspace).filter(pk__in=label_ids)
            )
        return instance


class TaskMoveSerializer(serializers.Serializer):
    """Drag-and-drop: move task to a column / reorder / sprint vs backlog."""

    column_id = serializers.UUIDField(required=False, allow_null=True)
    board_position = serializers.FloatField(required=False)
    is_in_backlog = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        if "column_id" in validated_data:
            instance.column_id = validated_data["column_id"]
            if validated_data["column_id"] is not None:
                instance.is_in_backlog = False
        if "board_position" in validated_data:
            instance.board_position = validated_data["board_position"]
        if "is_in_backlog" in validated_data:
            instance.is_in_backlog = validated_data["is_in_backlog"]
            if instance.is_in_backlog:
                instance.column_id = None
        instance.save()
        return instance
