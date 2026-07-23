from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.calendar_events.models import CalendarEvent
from apps.projects.models import BoardColumn, Project
from apps.tasks.models import Task, TaskPriority, TaskType
from apps.workspaces.models import Workspace, WorkspaceMembership, WorkspaceRole


class Command(BaseCommand):
    help = "Seed demo user, workspace, project, tasks, and calendar events"

    def handle(self, *args, **options):
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email="demo@worktaskme.com",
                defaults={
                    "first_name": "Demo",
                    "last_name": "User",
                    "is_active": True,
                },
            )
            user.set_password("Demo1234!")
            user.first_name = user.first_name or "Demo"
            user.last_name = user.last_name or "User"
            user.save()

            workspace, _ = Workspace.objects.get_or_create(
                slug="worktaskme-demo",
                defaults={
                    "name": "WorkTaskMe Demo",
                    "description": "Sample workspace for local demos",
                    "owner": user,
                    "default_key_prefix": "WTM",
                },
            )
            if workspace.owner_id != user.id:
                workspace.owner = user
                workspace.save(update_fields=["owner", "updated_at"])

            WorkspaceMembership.objects.update_or_create(
                workspace=workspace,
                user=user,
                defaults={"role": WorkspaceRole.ADMIN, "is_active": True},
            )

            project, project_created = Project.objects.get_or_create(
                workspace=workspace,
                key="WTM",
                defaults={
                    "name": "Platform",
                    "description": "Core platform delivery",
                    "color": "#0F766E",
                    "lead": user,
                },
            )

            if project_created or not project.columns.exists():
                project.columns.all().delete()
                defaults = [
                    ("Backlog", BoardColumn.ColumnCategory.BACKLOG, 0),
                    ("To Do", BoardColumn.ColumnCategory.TODO, 1),
                    ("In Progress", BoardColumn.ColumnCategory.IN_PROGRESS, 2),
                    ("Review", BoardColumn.ColumnCategory.REVIEW, 3),
                    ("Done", BoardColumn.ColumnCategory.DONE, 4),
                ]
                BoardColumn.objects.bulk_create(
                    [
                        BoardColumn(
                            workspace=workspace,
                            project=project,
                            name=name,
                            category=cat,
                            position=pos,
                        )
                        for name, cat, pos in defaults
                    ]
                )

            columns = {
                c.category: c for c in project.columns.all()
            }
            today = timezone.localdate()

            samples = [
                {
                    "title": "Design workspace switcher",
                    "priority": TaskPriority.HIGH,
                    "points": 5,
                    "column": columns.get(BoardColumn.ColumnCategory.DONE),
                    "backlog": False,
                    "due": today - timedelta(days=2),
                },
                {
                    "title": "Implement JWT auth flow",
                    "priority": TaskPriority.HIGHEST,
                    "points": 8,
                    "column": columns.get(BoardColumn.ColumnCategory.DONE),
                    "backlog": False,
                    "due": today - timedelta(days=1),
                },
                {
                    "title": "Kanban drag-and-drop API",
                    "priority": TaskPriority.HIGH,
                    "points": 5,
                    "column": columns.get(BoardColumn.ColumnCategory.REVIEW),
                    "backlog": False,
                    "due": today,
                },
                {
                    "title": "Team calendar sync",
                    "priority": TaskPriority.MEDIUM,
                    "points": 8,
                    "column": columns.get(BoardColumn.ColumnCategory.IN_PROGRESS),
                    "backlog": False,
                    "due": today + timedelta(days=2),
                },
                {
                    "title": "FCM push notifications",
                    "priority": TaskPriority.MEDIUM,
                    "points": 5,
                    "column": columns.get(BoardColumn.ColumnCategory.TODO),
                    "backlog": False,
                    "due": today + timedelta(days=5),
                },
                {
                    "title": "Sprint planning polish",
                    "priority": TaskPriority.LOW,
                    "points": 3,
                    "column": None,
                    "backlog": True,
                    "due": today + timedelta(days=10),
                },
                {
                    "title": "Bug: timezone on due dates",
                    "priority": TaskPriority.HIGH,
                    "points": 2,
                    "column": None,
                    "backlog": True,
                    "due": today + timedelta(days=3),
                    "task_type": TaskType.BUG,
                },
            ]

            if not Task.objects.filter(workspace=workspace, project=project).exists():
                for i, sample in enumerate(samples):
                    Task.create_with_key(
                        project=project,
                        workspace=workspace,
                        title=sample["title"],
                        description=f"Demo task: {sample['title']}",
                        task_type=sample.get("task_type", TaskType.TASK),
                        priority=sample["priority"],
                        story_points=sample["points"],
                        column=sample["column"],
                        is_in_backlog=sample["backlog"],
                        board_position=float(i),
                        reporter=user,
                        assignee=user,
                        due_date=sample["due"],
                        start_date=sample["due"] - timedelta(days=1)
                        if sample["due"]
                        else None,
                    )

            CalendarEvent.objects.get_or_create(
                workspace=workspace,
                title="Sprint Planning",
                start_at=today + timedelta(days=1),
                defaults={
                    "end_at": today + timedelta(days=1),
                    "all_day": True,
                    "color": "#0EA5E9",
                    "department": "Engineering",
                    "project": project,
                    "assignee": user,
                    "created_by": user,
                    "source": CalendarEvent.Source.MEETING,
                    "description": "Plan next sprint with the team",
                },
            )
            CalendarEvent.objects.get_or_create(
                workspace=workspace,
                title="Design Review",
                start_at=today + timedelta(days=3),
                defaults={
                    "end_at": today + timedelta(days=3),
                    "all_day": True,
                    "color": "#F59E0B",
                    "department": "Design",
                    "project": project,
                    "assignee": user,
                    "created_by": user,
                    "source": CalendarEvent.Source.MEETING,
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"  Email:     demo@worktaskme.com")
        self.stdout.write(f"  Password:  Demo1234!")
        self.stdout.write(f"  Workspace: {workspace.id}")
        self.stdout.write(f"  Project:   {project.key} ({project.id})")
        self.stdout.write(
            self.style.NOTICE(
                "Login via POST /api/auth/token/ then send X-Workspace-Id header."
            )
        )
