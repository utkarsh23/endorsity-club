from django.urls import path

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from notifications.consumers import NotificationConsumer


application = ProtocolTypeRouter({
    'websocket':
        AuthMiddlewareStack(
            URLRouter(
                [
                    path('ws/notifications/', NotificationConsumer),
                ]
            )
        )
})
