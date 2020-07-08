from django import template

from accounts.models import Brand

from brand.models import Campaign

from influencer.models import EndorsingPost

register = template.Library()

@register.filter
def is_subscription_active(user):
    return Brand.objects.get(user=user).is_subscription_active

@register.simple_tag
def posts(campaign):
    return EndorsingPost.objects.filter(campaign=campaign, complete=True).count()

@register.simple_tag
def check_active_campaign(campaign):
    if not campaign.brand.is_subscription_active:
        return False
    current_campaign = (Campaign.objects.filter(brand=campaign.brand)
                        .order_by('-start_time').first())
    return campaign == current_campaign
