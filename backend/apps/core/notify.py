from apps.core.models import Notification


def notify(*, workspace, user, title, body="", kind=Notification.Kind.SYSTEM, link="", meta=None):
    if user is None:
        return None
    return Notification.objects.create(
        workspace=workspace,
        user=user,
        title=title,
        body=body,
        kind=kind,
        link=link or "",
        meta=meta or {},
    )
