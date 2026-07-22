from django.conf import settings
from django.db import models

from apps.core.models import TenantModel


class CalendarEvent(TenantModel):
    """
    TeamUp-style calendar entry.

    source='task' rows are auto-synced from Task due/start dates.
    source='manual' rows are standalone meetings / blocks.
    """

    class Source(models.TextChoices):
        TASK = "task", "Task"
        MANUAL = "manual", "Manual"
        MEETING = "meeting", "Meeting"

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    start_at = models.DateField(db_index=True)
    end_at = models.DateField(db_index=True)
    all_day = models.BooleanField(default=True)
    # Optional time-of-day for non-all-day events (stored as HH:MM)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    color = models.CharField(max_length=7, default="#0EA5E9")
    department = models.CharField(max_length=100, blank=True)

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calendar_events",
    )
    task = models.OneToOneField(
        "tasks.Task",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calendar_event",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calendar_events",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_calendar_events",
    )
    source = models.CharField(
        max_length=16, choices=Source.choices, default=Source.MANUAL
    )

    class Meta:
        ordering = ["start_at", "start_time"]
        indexes = [
            models.Index(fields=["workspace", "start_at", "end_at"]),
            models.Index(fields=["workspace", "assignee"]),
            models.Index(fields=["workspace", "project"]),
            models.Index(fields=["workspace", "source"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.end_at < self.start_at:
            raise ValidationError({"end_at": "End date must be on or after start date."})
