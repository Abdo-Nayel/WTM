from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "auth_provider",
        "email_verified",
        "is_staff",
        "is_active",
    )
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_staff", "is_active", "email_verified", "auth_provider")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "avatar", "phone")}),
        (
            "Auth",
            {"fields": ("auth_provider", "email_verified", "is_active", "is_staff", "is_superuser")},
        ),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Push", {"fields": ("fcm_tokens",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "email_verified",
                ),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")
