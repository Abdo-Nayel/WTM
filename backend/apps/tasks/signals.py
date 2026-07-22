"""
Keep CalendarEvent in sync when Task due/start dates change.
Send in-app + email notification when a task is assigned / reassigned.

IMPORTANT: Never let calendar/notify side-effects break Task.save() —
that surfaces as a generic HTML 500 ("Server error") in the SPA.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.tasks.models import Task


@receiver(pre_save, sender=Task)
def cache_previous_assignee(sender, instance: Task, **kwargs):
    if not instance.pk:
        instance._previous_assignee_id = None
        return
    try:
        previous = (
            Task.objects.filter(pk=instance.pk)
            .values_list("assignee_id", flat=True)
            .first()
        )
        instance._previous_assignee_id = previous
    except Exception:  # pragma: no cover
        instance._previous_assignee_id = None


@receiver(post_save, sender=Task)
def sync_calendar_on_task_save(sender, instance: Task, created, **kwargs):
    try:
        _sync_calendar(instance)
    except Exception as exc:  # pragma: no cover
        if settings.DEBUG:
            print(f"[WorkTaskMe] calendar sync failed for {instance.issue_key}: {exc}")

    try:
        _notify_assignee(instance, created=created)
    except Exception as exc:  # pragma: no cover
        if settings.DEBUG:
            print(f"[WorkTaskMe] assign notify failed for {instance.issue_key}: {exc}")


def _sync_calendar(instance: Task):
    from apps.calendar_events.models import CalendarEvent

    if instance.due_date is None and instance.start_date is None:
        CalendarEvent.objects.filter(task=instance, source=CalendarEvent.Source.TASK).delete()
        return

    start = instance.start_date or instance.due_date
    end = instance.due_date or instance.start_date
    if start and end and end < start:
        start, end = end, start
    color = instance.project.color if instance.project_id else "#2563EB"
    title = f"{instance.issue_key}: {instance.title}"[:500]
    description = (instance.description or "")[:2000]

    # task is OneToOne — lookup by task only to avoid UNIQUE conflicts
    CalendarEvent.objects.update_or_create(
        task=instance,
        defaults={
            "workspace": instance.workspace,
            "project": instance.project,
            "source": CalendarEvent.Source.TASK,
            "title": title,
            "description": description,
            "start_at": start,
            "end_at": end,
            "all_day": True,
            "color": color,
            "assignee": instance.assignee,
        },
    )


def _notify_assignee(instance: Task, *, created: bool):
    from apps.core.models import Notification
    from apps.core.notify import notify

    previous_assignee_id = getattr(instance, "_previous_assignee_id", None)
    new_assignee_id = instance.assignee_id
    assignee_changed = bool(new_assignee_id) and (
        created or str(previous_assignee_id or "") != str(new_assignee_id)
    )
    if not assignee_changed or not instance.assignee:
        return

    notify(
        workspace=instance.workspace,
        user=instance.assignee,
        kind=Notification.Kind.TASK,
        title=f"Assigned {instance.issue_key}",
        body=instance.title,
        link="/?tab=board",
        meta={"task_id": str(instance.id), "issue_key": instance.issue_key},
    )

    email = (instance.assignee.email or "").strip()
    if not email:
        return

    workspace_name = getattr(instance.workspace, "name", "WorkTaskMe")
    subject = f"[{workspace_name}] Assigned: {instance.issue_key}"
    body = (
        f"You were assigned to {instance.issue_key}: {instance.title}\n\n"
        f"Workspace: {workspace_name}\n"
        f"Project: {getattr(instance.project, 'name', '')}\n"
        f"Priority: {instance.priority}\n"
        f"Open: {settings.FRONTEND_URL}/\n\n"
        f"— WorkTaskMe\n"
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True,
    )
    if settings.DEBUG:
        print(f"\n[WorkTaskMe ASSIGN EMAIL] to={email} task={instance.issue_key}\n{body}\n")


@receiver(post_delete, sender=Task)
def delete_calendar_on_task_delete(sender, instance: Task, **kwargs):
    from apps.calendar_events.models import CalendarEvent

    try:
        CalendarEvent.objects.filter(task_id=instance.id, source=CalendarEvent.Source.TASK).delete()
    except Exception:  # pragma: no cover
        pass
