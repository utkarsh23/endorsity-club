from django import template

from accounts.models import Influencer

register = template.Library()

@register.filter
def is_influencer_unlocked(user):
    return Influencer.objects.get(user=user).is_unlocked
