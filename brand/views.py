import datetime
import json
import pytz
import requests
import urllib.parse

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect

from accounts.models import Brand, Location

from brand.forms import AddLocationForm
from brand.mixins import RegisteredBrandLoginRequiredMixin
from brand.models import Campaign
from brand.tasks import end_subscription

from notifications.models import Notification


class YourEndorsementsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/your-endorsements.html'


class ProfileView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = Brand.objects.get(user=self.request.user)
        context['brand'] = brand
        context['locations'] = Location.objects.filter(brand=brand)
        return context


class QRCodeView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/qr_code.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand_id'] = Brand.objects.get(user=self.request.user).id
        return context


class AddLocationView(RegisteredBrandLoginRequiredMixin, FormView):
    form_class = AddLocationForm
    template_name = 'brand/add_location.html'
    success_url = reverse_lazy('brand:profile')

    def form_valid(self, form):
        store_location = form.cleaned_data['store_location']
        try:
            GEOCODE_URI = (settings.GOOGLE_MAPS_URI +
                f'?address={urllib.parse.quote_plus(store_location)}' +
                f'&key={settings.GOOGLE_MAPS_SERVER_API_KEY}')
            resp = json.loads(requests.get(GEOCODE_URI).text)
            lat_lng = resp['results'][0]['geometry']['location']
            for component in resp['results'][0]['address_components']:
                if 'locality' in component['types']:
                    city = component['long_name']
                    break
        except:
            return super().form_invalid(form)
        brand = Brand.objects.get(user=self.request.user)
        location = Location.objects.create(
            brand=brand,
            name=store_location,
            latitude=lat_lng['lat'],
            longitude=lat_lng['lng'],
            city=city,
        )
        return super().form_valid(form)


class CampaignsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/campaigns.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = Brand.objects.get(user=self.request.user)
        campaigns = (Campaign.objects.filter(brand=brand)
                    .order_by('-start_time'))
        if brand.is_subscription_active:
            current_campaign = campaigns.first()
            context['current_campaign'] = current_campaign
            campaigns = campaigns[1:]
        context['past_campaigns'] = campaigns
        return context


class InitiateCampaignView(RegisteredBrandLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        brand = Brand.objects.get(user=request.user)
        if not brand.is_subscription_active:
            start_time = datetime.datetime.now()
            end_time = start_time + settings.PAID_SUBSCRIPTION_TIME
            end_time =(end_time.astimezone(pytz.timezone('Asia/Kolkata'))
                        .replace(hour=23, minute=59, second=59, microsecond=59))
            Campaign.objects.create(
                brand=brand,
                start_time=start_time,
                end_time=end_time,
            )
            brand.is_subscription_active = True
            brand.save()
            end_subscription.apply_async(args=[brand.user.pk], eta=end_time)
        return redirect(reverse_lazy('brand:campaigns'))


class CampaignDetailsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/campaign_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = Campaign.objects.get(id=kwargs['campaign_uuid'])
        if campaign.brand.user != self.request.user:
            raise PermissionDenied
        context['campaign'] = campaign
        context['active_locations'] = Location.objects.filter(brand=campaign.brand, active=True)
        context['inactive_locations'] = Location.objects.filter(brand=campaign.brand, active=False)
        return context
