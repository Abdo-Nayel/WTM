from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.calendar_events.models import CalendarEvent


class CalendarEventSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )
    project_id = serializers.UUIDField(
        write_only=True, required=False, allow_null=True
    )
    task_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = CalendarEvent
        fields = (
            "id",
            "title",
            "description",
            "start_at",
            "end_at",
            "all_day",
            "start_time",
            "end_time",
            "color",
            "department",
            "project",
            "project_id",
            "task",
            "task_id",
            "assignee",
            "assignee_id",
            "created_by",
            "source",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "project",
            "task",
            "assignee",
            "created_by",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        start = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_at": "End date must be on or after start date."}
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        assignee_id = validated_data.pop("assignee_id", None)
        project_id = validated_data.pop("project_id", None)
        task_id = validated_data.pop("task_id", None)
        # TenantViewSetMixin may inject workspace into validated_data
        validated_data.pop("workspace", None)
        source = validated_data.pop("source", None) or CalendarEvent.Source.MANUAL
        return CalendarEvent.objects.create(
            workspace=request.workspace,
            created_by=request.user,
            assignee_id=assignee_id,
            project_id=project_id,
            task_id=task_id,
            source=source,
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data.pop("workspace", None)
        if instance.source == CalendarEvent.Source.TASK:
            # Task-synced events: allow scheduling + cosmetic fields
            allowed = {
                "color",
                "department",
                "description",
                "title",
                "start_at",
                "end_at",
                "all_day",
                "start_time",
                "end_time",
            }
            validated_data = {k: v for k, v in validated_data.items() if k in allowed}
        for field in ("assignee_id", "project_id", "task_id"):
            if field in validated_data:
                setattr(instance, field, validated_data.pop(field))
        return super().update(instance, validated_data)
