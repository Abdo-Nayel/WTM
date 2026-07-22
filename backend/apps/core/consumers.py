"""
Realtime consumers for Kanban boards and calendar.

Clients connect to:
  ws://host/ws/workspace/<uuid>/board/
  ws://host/ws/workspace/<uuid>/calendar/

Messages are JSON: {"type": "task.moved", "payload": {...}}
"""
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class WorkspaceConsumerBase(AsyncJsonWebsocketConsumer):
    group_prefix = "workspace"

    async def connect(self):
        self.workspace_id = self.scope["url_route"]["kwargs"]["workspace_id"]
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close(code=4001)
            return

        allowed = await self._user_in_workspace(user.id, self.workspace_id)
        if not allowed:
            await self.close(code=4003)
            return

        self.group_name = f"{self.group_prefix}_{self.workspace_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Echo/broadcast client events (e.g. drag preview); persist via REST.
        event_type = content.get("type", "message")
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "workspace.event",
                "event_type": event_type,
                "payload": content.get("payload", {}),
                "sender": str(self.scope["user"].id),
            },
        )

    async def workspace_event(self, event):
        await self.send_json(
            {
                "type": event["event_type"],
                "payload": event["payload"],
                "sender": event.get("sender"),
            }
        )

    @database_sync_to_async
    def _user_in_workspace(self, user_id, workspace_id):
        from apps.workspaces.models import WorkspaceMembership

        return WorkspaceMembership.objects.filter(
            user_id=user_id, workspace_id=workspace_id, is_active=True
        ).exists()


class BoardConsumer(WorkspaceConsumerBase):
    group_prefix = "board"


class CalendarConsumer(WorkspaceConsumerBase):
    group_prefix = "calendar"


def broadcast_workspace_event(channel_layer, group_prefix, workspace_id, event_type, payload):
    """Helper for views/signals to push updates (call from sync context via async_to_sync)."""
    from asgiref.sync import async_to_sync

    async_to_sync(channel_layer.group_send)(
        f"{group_prefix}_{workspace_id}",
        {
            "type": "workspace.event",
            "event_type": event_type,
            "payload": payload,
            "sender": "server",
        },
    )
