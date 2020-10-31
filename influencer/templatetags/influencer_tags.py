from django import template

from accounts.models import Influencer

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
