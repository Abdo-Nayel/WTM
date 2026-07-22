import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel, UUIDModel


class WorkspaceRole(models.TextChoices):
    ADMIN = "admin", "Workspace Admin"
    PROJECT_MANAGER = "project_manager", "Project Manager"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class Workspace(UUIDModel, TimeStampedModel):
    """
    Top-level tenant. All domain data hangs off workspace_id.

    Single-database multi-tenancy: one Postgres, many workspaces,
    isolation via FK + membership checks (not separate schemas).
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="workspace_logos/", blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_workspaces",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    # Default project key prefix used when creating projects (e.g. WTM)
    default_key_prefix = models.CharField(max_length=10, default="WTM")

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "created_at"]),
        ]

    def __str__(self):
        return self.name


class WorkspaceMembership(UUIDModel, TimeStampedModel):
    """Join table: User ↔ Workspace with RBAC role."""

    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(
        max_length=32,
        choices=WorkspaceRole.choices,
        default=WorkspaceRole.MEMBER,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_workspace_invites_accepted",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"],
                name="uniq_workspace_user_membership",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "role"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.workspace} ({self.role})"


class WorkspaceInvitation(UUIDModel, TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField(db_index=True)
    role = models.CharField(
        max_length=32,
        choices=WorkspaceRole.choices,
        default=WorkspaceRole.MEMBER,
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_invitations_sent",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["workspace", "email"]),
        ]

    @classmethod
    def create_invite(cls, workspace, email, role, invited_by, days_valid=7):
        return cls.objects.create(
            workspace=workspace,
            email=email.lower().strip(),
            role=role,
            invited_by=invited_by,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timezone.timedelta(days=days_valid),
        )

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_accepted(self):
        return self.accepted_at is not None

    def __str__(self):
        return f"Invite {self.email} → {self.workspace}"
