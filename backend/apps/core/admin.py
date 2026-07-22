from django.contrib import admin

from apps.core.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "workspace", "kind", "is_read", "created_at")
    list_filter = ("kind", "is_read", "created_at")
    search_fields = ("title", "body", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("workspace", "user")
