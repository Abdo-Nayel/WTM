from django.conf import settings
from django.db import models

from apps.core.models import TenantModel


class Project(TenantModel):
    """Jira-style project inside a workspace."""

    name = models.CharField(max_length=200)
    key = models.CharField(max_length=10)  # e.g. WTM — used for WTM-101
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#2563EB")  # hex
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_projects",
    )
    is_archived = models.BooleanField(default=False, db_index=True)
    # Auto-increment counter for issue keys within this project
    next_issue_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "key"],
                name="uniq_project_key_per_workspace",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "is_archived"]),
        ]

    def __str__(self):
        return f"{self.key} — {self.name}"

    def allocate_issue_number(self) -> int:
        """Atomically allocate next issue number (call inside transaction)."""
        project = Project.objects.select_for_update().get(pk=self.pk)
        number = project.next_issue_number
        project.next_issue_number = number + 1
        project.save(update_fields=["next_issue_number", "updated_at"])
        self.next_issue_number = project.next_issue_number
        return number


class Epic(TenantModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="epics"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#7C3AED")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["workspace", "project"]),
        ]

    def __str__(self):
        return self.name


class Label(TenantModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="labels",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=7, default="#64748B")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "name", "project"],
                name="uniq_label_name_project_workspace",
            )
        ]

    def __str__(self):
        return self.name


class BoardColumn(TenantModel):
    """Kanban / Scrum column (status lane)."""

    class ColumnCategory(models.TextChoices):
        BACKLOG = "backlog", "Backlog"
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        REVIEW = "review", "Review"
        DONE = "done", "Done"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="columns"
    )
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=32,
        choices=ColumnCategory.choices,
        default=ColumnCategory.TODO,
    )
    position = models.PositiveIntegerField(default=0)
    wip_limit = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position", "name"]
        indexes = [
            models.Index(fields=["workspace", "project", "position"]),
        ]

    def __str__(self):
        return f"{self.project.key}:{self.name}"
