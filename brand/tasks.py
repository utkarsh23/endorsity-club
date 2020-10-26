from django.core import serializers
from django.contrib.auth import get_user_model

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from endorsity.celery import app

from accounts.models import Brand, Influencer

from notifications.models import Notification
from notifications.utils import create_and_broadcast_notification


@app.task
def end_subscription(user_pk):
    brand = Brand.objects.get(user__pk=user_pk)
    brand.is_subscription_active = False
    brand.save()

@app.task
def notify_influencers(user_pk):
    channel_layer = get_channel_layer()
    user_model = get_user_model()
    brand = Brand.objects.get(user__pk=user_pk)
    message = f"{brand.name} is now on Endorsity!"
    link = f"/influencer/brand/{brand.id}"
    for influencer in Influencer.objects.all():
        create_and_broadcast_notification(influencer.user.pk, message, link)
