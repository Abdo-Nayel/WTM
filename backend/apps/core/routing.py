"""WebSocket routing for real-time board / calendar updates."""
from django.urls import re_path

from apps.core import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/workspace/(?P<workspace_id>[0-9a-f-]+)/board/$",
        consumers.BoardConsumer.as_asgi(),
    ),
    re_path(
        r"ws/workspace/(?P<workspace_id>[0-9a-f-]+)/calendar/$",
        consumers.CalendarConsumer.as_asgi(),
    ),
]
