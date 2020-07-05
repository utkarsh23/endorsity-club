from django import template
from django.db.models import Q

from notifications.models import Notification

register = template.Library()

@register.simple_tag
def notifications(user):
    return (Notification.objects.filter(user=user)
            .order_by('-created_at'))[:8]

@register.simple_tag
def notifs_unread(user):
    return (Notification.objects
            .filter(Q(user=user) & Q(is_seen=False)).count())
