from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Migrate, seed demo data, and print local URLs + credentials"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Running migrations…"))
        call_command("migrate", interactive=False)

        self.stdout.write(self.style.NOTICE("Seeding demo data…"))
        call_command("seed_demo")

        host = "http://127.0.0.1:8000"
        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:8080")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Local bootstrap complete."))
        self.stdout.write("")
        self.stdout.write("  API:        " + host + "/api/")
        self.stdout.write("  Docs:       " + host + "/api/docs/")
        self.stdout.write("  Health:     " + host + "/api/health/")
        self.stdout.write("  Admin:      " + host + "/admin/")
        self.stdout.write("  Frontend:   " + frontend)
        self.stdout.write("")
        self.stdout.write("  Email:      demo@worktaskme.com")
        self.stdout.write("  Password:   Demo1234!")
        self.stdout.write("")
        self.stdout.write(
            self.style.NOTICE(
                "Login: POST /api/auth/token/ then send X-Workspace-Id on tenant routes."
            )
        )
