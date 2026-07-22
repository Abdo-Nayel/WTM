from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.calendar_events.models import CalendarEvent
from apps.calendar_events.serializers import CalendarEventSerializer
from apps.core.mixins import TenantViewSetMixin
from apps.workspaces.models import WorkspaceRole


class CalendarEventFilter(filters.FilterSet):
    project = filters.UUIDFilter(field_name="project_id")
    assignee = filters.UUIDFilter(field_name="assignee_id")
    source = filters.CharFilter()
    department = filters.CharFilter()
    start = filters.DateFilter(field_name="end_at", lookup_expr="gte")
    end = filters.DateFilter(field_name="start_at", lookup_expr="lte")

    class Meta:
        model = CalendarEvent
        fields = ["project", "assignee", "source", "department"]


class CalendarEventViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    TeamUp-style calendar API.

    Query range: ?start=2026-07-01&end=2026-07-31
    Resource timeline: ?assignee=<uuid>
    """

    serializer_class = CalendarEventSerializer
    queryset = CalendarEvent.objects.select_related(
        "assignee", "project", "task", "created_by"
    )
    filterset_class = CalendarEventFilter
    search_fields = ("title", "description", "department")
    ordering_fields = ("start_at", "end_at", "created_at")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            self.required_role = WorkspaceRole.MEMBER
        else:
            self.required_role = WorkspaceRole.VIEWER
        return super().get_permissions()

    def perform_destroy(self, instance):
        if instance.source == CalendarEvent.Source.TASK:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "Cannot delete a task-synced event. Clear the task due date instead."
            )
        super().perform_destroy(instance)

    @action(detail=False, methods=["get"])
    def timeline(self, request):
        """
        Resource timeline: events grouped by assignee for TeamUp-style view.
        """
        qs = self.filter_queryset(self.get_queryset())
        grouped = {}
        for event in qs:
            key = str(event.assignee_id) if event.assignee_id else "unassigned"
            grouped.setdefault(
                key,
                {
                    "assignee": (
                        {
                            "id": str(event.assignee_id),
                            "email": event.assignee.email,
                            "full_name": event.assignee.full_name,
                        }
                        if event.assignee_id
                        else None
                    ),
                    "events": [],
                },
            )
            grouped[key]["events"].append(
                CalendarEventSerializer(event, context={"request": request}).data
            )
        return Response(list(grouped.values()))
