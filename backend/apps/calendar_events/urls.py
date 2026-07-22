from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.calendar_events.views import CalendarEventViewSet

router = DefaultRouter()
router.register(r"events", CalendarEventViewSet, basename="calendar-event")

urlpatterns = [
    path("", include(router.urls)),
]
