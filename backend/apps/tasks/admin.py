from django.contrib import admin

from apps.tasks.models import Task, TaskActivity, TaskAttachment, TaskComment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "issue_key",
        "title",
        "project",
        "priority",
        "assignee",
        "is_in_backlog",
        "due_date",
    )
    list_filter = ("priority", "task_type", "is_in_backlog")
    search_fields = ("issue_key", "title")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ("task", "action", "actor", "created_at")


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "kind", "task", "size_bytes", "created_at")
    list_filter = ("kind",)
