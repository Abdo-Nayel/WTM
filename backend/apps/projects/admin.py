from django.contrib import admin

from apps.projects.models import BoardColumn, Epic, Label, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "workspace", "lead", "is_archived")
    list_filter = ("is_archived",)
    search_fields = ("name", "key")


@admin.register(Epic)
class EpicAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "workspace", "is_done")


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "project", "workspace")


@admin.register(BoardColumn)
class BoardColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "project", "position")
    list_filter = ("category",)
