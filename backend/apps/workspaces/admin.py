from django.contrib import admin

from apps.workspaces.models import Workspace, WorkspaceInvitation, WorkspaceMembership


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ("workspace", "user", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "workspace__name")


@admin.register(WorkspaceInvitation)
class WorkspaceInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "workspace", "role", "expires_at", "accepted_at")
    search_fields = ("email", "workspace__name")
