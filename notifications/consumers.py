import json

from django.core import serializers

from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer
from channels.generic.websocket import WebsocketConsumer

from notifications.models import Notification

from accounts.models import User


class NotificationConsumer(WebsocketConsumer):

    def connect(self):
        """Authenticate the user and accept the connection"""

        if self.scope['user'].is_authenticated:

            # Add the user to the group id = user_id
            self.group_name = f'notification_{self.scope["user"].id}'
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )

            self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """ Receive all the requests to the socket """
        functions = {
            'all_seen': self.all_seen,
        }
        json_data = json.loads(text_data)
        functions[json_data['function']]()

    def receive_notification(self, args):
        """
        1. Receive a notification from another socket
        2. Send the notification received to the frontend
        Requires the following properties in args:
        1. notifs : List of notifications received
        """
        user_id = args['user_id']
        message = args['message']
        link = args['link']
        channel_layer = get_channel_layer()
        notification = Notification.objects.create(
            user=User.objects.get(pk=user_id),
            message=message,
            link=link,
        )
        self.send(text_data=json.dumps({
            "function": "new_notifications_received",
            "arguments": {
                "notifs": [serializers.serialize('json', [notification, ]), ],
            }
        }))
    
    def all_seen(self):
        Notification.objects.filter(user=self.scope['user']).update(is_seen=True)
