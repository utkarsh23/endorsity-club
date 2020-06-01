from django.urls import path

from notifications.views import NotificationsView

urlpatterns = [
    path("", NotificationsView.as_view(), name="notification_page"),
]
