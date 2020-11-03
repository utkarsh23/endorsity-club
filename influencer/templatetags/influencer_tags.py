from django import template
from django.conf import settings

from accounts.models import Influencer, FacebookPermissions

register = template.Library()

@register.filter
def is_influencer_unlocked(user):
    return Influencer.objects.get(user=user).is_unlocked

@register.filter
def readable_metric(number_as_string):
    if not number_as_string:
        return '...'
    number = int(number_as_string)
    million = [1000000, 'M']
    thousand = [1000, 'K']
    if number > million[0]:
        rounding = million
    elif number > thousand[0]:
        rounding = thousand
    else:
        return number
    final_metric = int((number / rounding[0]) * 10) / 10
    if str(final_metric).split('.')[-1] == '0':
        final_metric = int(final_metric)
    return f"{final_metric}{rounding[1]}"

@register.filter
def influencer_category(influencer):
    follower_count = int(FacebookPermissions.objects.get(influencer=influencer).ig_follower_count)
    if follower_count >= settings.GOLD_CATEGORY[0]:
        return 'gold'
    elif follower_count >= settings.SILVER_CATEGORY[0]:
        return 'silver'
    else:
        return 'bronze'

@register.filter
def influencer_discount(influencer):
    follower_count = int(FacebookPermissions.objects.get(influencer=influencer).ig_follower_count)
    if follower_count >= settings.GOLD_CATEGORY[0]:
        return '15,000'
    elif follower_count >= settings.SILVER_CATEGORY[0]:
        return '10,000'
    else:
        return '5,000'
