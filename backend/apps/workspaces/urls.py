from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.workspaces.views import AcceptInviteView, InvitePreviewView, WorkspaceViewSet

router = DefaultRouter()
router.register(r"", WorkspaceViewSet, basename="workspace")

urlpatterns = [
    path("invitations/accept/", AcceptInviteView.as_view(), name="invite-accept"),
    path(
        "invitations/<str:token>/preview/",
        InvitePreviewView.as_view(),
        name="invite-preview",
    ),
    path("", include(router.urls)),
]
