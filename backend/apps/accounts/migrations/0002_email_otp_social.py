import uuid

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="auth_provider",
            field=models.CharField(
                choices=[
                    ("email", "Email"),
                    ("google", "Google"),
                    ("microsoft", "Microsoft"),
                ],
                default="email",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="EmailOTP",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("code_hash", models.CharField(max_length=64)),
                (
                    "purpose",
                    models.CharField(
                        choices=[("register", "Register"), ("login", "Login")],
                        default="register",
                        max_length=16,
                    ),
                ),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # Existing demo users should remain usable after migrate
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model("accounts", "User")
            .objects.filter(is_active=True)
            .update(email_verified=True),
            reverse_code=migrations.RunPython.noop,
        ),
    ]
