from django.contrib import admin

from apps.calendar_events.models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "workspace",
        "start_at",
        "end_at",
        "source",
        "assignee",
        "project",
    )
    list_filter = ("source", "all_day", "department")
    search_fields = ("title",)
