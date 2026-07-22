from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import Notification
from apps.core.permissions import (
    HasWorkspaceAccess,
    IsAuthenticatedAndActive,
)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "title",
            "body",
            "link",
            "is_read",
            "meta",
            "created_at",
        )
        read_only_fields = fields


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticatedAndActive, HasWorkspaceAccess]

    def get_queryset(self):
        workspace = getattr(self.request, "workspace", None)
        if workspace is None:
            return Notification.objects.none()
        return Notification.objects.for_workspace(workspace).filter(
            user=self.request.user
        )

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        qs = self.get_queryset().filter(is_read=False)
        updated = qs.update(is_read=True)
        return Response({"updated": updated})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(n).data)
