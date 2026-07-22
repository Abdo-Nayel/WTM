"""
Base models for multi-tenant isolation.

All domain entities that belong to a workspace MUST inherit TenantModel.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.managers import TenantManager


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TenantModel(UUIDModel, TimeStampedModel):
    """
    Abstract base for every row that is isolated by workspace.

    Convention:
      - FK name is always `workspace`
      - Queries go through TenantManager.for_workspace(...)
      - Views enforce membership via WorkspacePermission
    """

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        db_index=True,
    )

    objects = TenantManager()

    class Meta:
        abstract = True
        indexes = [
            # Concrete subclasses should add composite indexes as needed.
        ]

    def save(self, *args, **kwargs):
        if self.workspace_id is None:
            raise ValueError(f"{self.__class__.__name__} requires a workspace.")
        super().save(*args, **kwargs)


class Notification(TenantModel):
    """In-app notification (invites also send email via console/SMTP)."""

    class Kind(models.TextChoices):
        INVITE = "invite", "Invite"
        TASK = "task", "Task"
        MENTION = "mention", "Mention"
        SYSTEM = "system", "System"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.SYSTEM)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} → {self.user}"

