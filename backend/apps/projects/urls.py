from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.projects.views import (
    BoardColumnViewSet,
    EpicViewSet,
    LabelViewSet,
    ProjectViewSet,
)

router = DefaultRouter()
router.register(r"epics", EpicViewSet, basename="epic")
router.register(r"labels", LabelViewSet, basename="label")
router.register(r"columns", BoardColumnViewSet, basename="column")
router.register(r"", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
]
