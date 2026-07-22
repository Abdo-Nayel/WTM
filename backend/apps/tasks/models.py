from django.conf import settings
from django.db import models, transaction

from apps.core.models import TenantModel


class TaskPriority(models.TextChoices):
    LOWEST = "lowest", "Lowest"
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    HIGHEST = "highest", "Highest"


class TaskType(models.TextChoices):
    STORY = "story", "Story"
    TASK = "task", "Task"
    BUG = "bug", "Bug"
    SUBTASK = "subtask", "Sub-task"


class Task(TenantModel):
    """
    Jira-style work item.

    issue_key is denormalized as PROJECTKEY-NUMBER (e.g. WTM-101).
    parent != null → sub-task.
    """

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="tasks"
    )
    epic = models.ForeignKey(
        "projects.Epic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtasks",
    )
    column = models.ForeignKey(
        "projects.BoardColumn",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    issue_number = models.PositiveIntegerField()
    issue_key = models.CharField(max_length=32, db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    task_type = models.CharField(
        max_length=16, choices=TaskType.choices, default=TaskType.TASK
    )
    priority = models.CharField(
        max_length=16, choices=TaskPriority.choices, default=TaskPriority.MEDIUM
    )
    story_points = models.PositiveSmallIntegerField(null=True, blank=True)
    board_position = models.FloatField(default=0)  # for drag-and-drop ordering
    is_in_backlog = models.BooleanField(default=True, db_index=True)

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    labels = models.ManyToManyField(
        "projects.Label", blank=True, related_name="tasks"
    )

    due_date = models.DateField(null=True, blank=True, db_index=True)
    start_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ["board_position", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "issue_key"],
                name="uniq_issue_key_per_workspace",
            ),
            models.UniqueConstraint(
                fields=["project", "issue_number"],
                name="uniq_issue_number_per_project",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace", "project", "column"]),
            models.Index(fields=["workspace", "assignee"]),
            models.Index(fields=["workspace", "is_in_backlog"]),
            models.Index(fields=["workspace", "due_date"]),
        ]

    def __str__(self):
        return f"{self.issue_key}: {self.title}"

    @classmethod
    def create_with_key(cls, *, project, workspace, **kwargs):
        with transaction.atomic():
            number = project.allocate_issue_number()
            issue_key = f"{project.key}-{number}"
            return cls.objects.create(
                project=project,
                workspace=workspace,
                issue_number=number,
                issue_key=issue_key,
                **kwargs,
            )


class TaskComment(TenantModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_comments",
    )
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.task.issue_key}"


class TaskActivity(TenantModel):
    """Audit trail for task changes (status moves, assignee, etc.)."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    action = models.CharField(max_length=64)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "task activities"


def task_attachment_upload_to(instance, filename):
    return f"attachments/{instance.workspace_id}/{instance.task_id}/{filename}"


class TaskAttachment(TenantModel):
    """Jira-style attachments: files, images (paste), audio, video."""

    class Kind(models.TextChoices):
        FILE = "file", "File"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio / Voice"
        VIDEO = "video", "Video"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_attachments",
    )
    file = models.FileField(upload_to=task_attachment_upload_to)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.FILE)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=128, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name or str(self.file)
