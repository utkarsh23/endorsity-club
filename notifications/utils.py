from django.core import serializers

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notifications.models import Notification

from accounts.models import User


def create_and_broadcast_notification(user_id, message, link):
    notification = Notification.objects.create(
        user=User.objects.get(pk=user_id),
        message=message,
        link=link,
    )
    async_to_sync(get_channel_layer().group_send)(
        f"notification_{user_id}",
        {
            "type":"receive_notification",
            "notification": [serializers.serialize('json', [notification, ]), ],
        },
    )
