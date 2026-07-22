from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.projects.models import BoardColumn, Epic, Label, Project


class BoardColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardColumn
        fields = (
            "id",
            "project",
            "name",
            "category",
            "position",
            "wip_limit",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ("id", "project", "name", "color", "created_at")
        read_only_fields = ("id", "created_at")


class EpicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Epic
        fields = (
            "id",
            "project",
            "name",
            "description",
            "color",
            "start_date",
            "end_date",
            "is_done",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "project", "created_at", "updated_at")


class ProjectSerializer(serializers.ModelSerializer):
    lead = UserSerializer(read_only=True)
    lead_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    columns = BoardColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "key",
            "description",
            "color",
            "lead",
            "lead_id",
            "is_archived",
            "next_issue_number",
            "columns",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "next_issue_number", "created_at", "updated_at")

    def validate_key(self, value):
        value = value.strip().upper()
        if not value.isalnum() or len(value) > 10:
            raise serializers.ValidationError(
                "Project key must be alphanumeric and ≤ 10 chars."
            )
        return value

    def create(self, validated_data):
        lead_id = validated_data.pop("lead_id", None)
        validated_data.pop("workspace", None)
        workspace = self.context["request"].workspace
        project = Project.objects.create(
            workspace=workspace,
            lead_id=lead_id,
            **validated_data,
        )
        # Seed default Kanban columns
        defaults = [
            ("Backlog", BoardColumn.ColumnCategory.BACKLOG, 0),
            ("To Do", BoardColumn.ColumnCategory.TODO, 1),
            ("In Progress", BoardColumn.ColumnCategory.IN_PROGRESS, 2),
            ("Review", BoardColumn.ColumnCategory.REVIEW, 3),
            ("Done", BoardColumn.ColumnCategory.DONE, 4),
        ]
        BoardColumn.objects.bulk_create(
            [
                BoardColumn(
                    workspace=workspace,
                    project=project,
                    name=name,
                    category=cat,
                    position=pos,
                )
                for name, cat, pos in defaults
            ]
        )
        return project

    def update(self, instance, validated_data):
        lead_id = validated_data.pop("lead_id", None)
        if "lead_id" in self.initial_data:
            instance.lead_id = lead_id
        return super().update(instance, validated_data)
