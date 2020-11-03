import datetime
import json
import pytz
import requests
import urllib.parse

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect

from accounts.mixins import RegisteredLoginRequiredMixin
from accounts.models import (
    Brand,
    Location,
    Influencer,
    FacebookPermissions,
)
from accounts.views import InfiniteAPIView

from brand.forms import AddLocationForm, ActiveLocationsForm
from brand.mixins import RegisteredBrandLoginRequiredMixin
from brand.models import Campaign
from brand.tasks import end_subscription

from influencer.models import (
    EndorsingPost,
    InfluencerStatistics,
)

from notifications.models import Notification


class ProfileView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = Brand.objects.get(user=self.request.user)
        context['base_template'] = 'brand/base.html'
        context['brand'] = brand
        context['locations'] = Location.objects.filter(brand=brand)
        context['endorsements'] = (EndorsingPost.objects
            .filter(campaign__brand__user=self.request.user, complete=True).order_by('-created_at'))
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
        city = ""
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
    template_name = 'brand/campaign.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = Brand.objects.get(user=self.request.user)
        if brand.is_subscription_active:
            current_campaign = (Campaign.objects.filter(brand=brand)
                    .order_by('-start_time').first())
            context['current_campaign'] = current_campaign
            context['locations'] = Location.objects.filter(brand=current_campaign.brand).order_by('id')
            context['posts'] = EndorsingPost.objects.filter(campaign=current_campaign, complete=True)
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
            # end_subscription.apply_async(args=[brand.user.pk], eta=end_time)
        return redirect(reverse_lazy('brand:campaign'))


class InfluencersView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/influencers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['your_influencers'] = (EndorsingPost.objects
            .filter(campaign__brand__user=self.request.user, complete=True)
            .distinct('influencer'))
        return context


class InfluencerAnalyticsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'influencer/profile_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = 'brand/base.html'
        influencer = (Influencer.objects
            .get(user__pk=urlsafe_base64_decode(force_text(kwargs['influencer_pk']))))
        context['influencer'] = influencer
        context['fb_permissions'] = (FacebookPermissions.objects
            .get(influencer=influencer))
        influencer_statistics = (InfluencerStatistics.objects
            .get(influencer=influencer))
        if influencer_statistics.audience_city:
            context['audience_city_stats'] = sorted(
                influencer_statistics.audience_city,
                reverse=True,
                key=lambda el: int(el[1]))[:3]
        if influencer_statistics.audience_gender_age:
            context['audience_demographic'] = [
                [el[0].replace('M.', 'Male ').replace('F.', 'Female ').replace('U.', 'Unknown '), int(el[1])]
                for el in influencer_statistics.audience_gender_age]
        if influencer_statistics.impressions:
            context['impressions'] = [
                [datetime.datetime.utcfromtimestamp(int(el[0])).strftime('%d %b %y'), int(el[1])]
                for el in influencer_statistics.impressions[::-1]]
        if influencer_statistics.follower_counts:
            context['follower_counts'] = [
                [datetime.datetime.utcfromtimestamp(int(el[0])).strftime('%d %b %y'), int(el[1])]
                for el in influencer_statistics.follower_counts[::-1]]
        return context


class InfluencerEndorsementsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'influencer/profile_endorsements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = 'brand/base.html'
        influencer = (Influencer.objects
            .get(user__pk=urlsafe_base64_decode(force_text(kwargs['influencer_pk']))))
        context['influencer'] = influencer
        context['fb_permissions'] = (FacebookPermissions.objects
            .get(influencer=influencer))
        context['endorsements'] = (EndorsingPost.objects
            .filter(influencer=influencer, complete=True).order_by('-created_at'))
        return context


class InfluencerBadgeView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'influencer/profile_badge.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = 'brand/base.html'
        influencer = (Influencer.objects
            .get(user__pk=urlsafe_base64_decode(force_text(kwargs['influencer_pk']))))
        context['influencer'] = influencer
        context['fb_permissions'] = (FacebookPermissions.objects
            .get(influencer=influencer))
        return context


class FetchInfluencersInfiniteAPIView(RegisteredBrandLoginRequiredMixin, InfiniteAPIView):
    pass


class EditActiveLocationsView(RegisteredBrandLoginRequiredMixin, FormView):
    template_name = 'brand/edit_active_locations.html'
    form_class = ActiveLocationsForm
    success_url = reverse_lazy('brand:campaign')

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        brand = Brand.objects.get(user=self.request.user)
        if not brand.is_subscription_active:
            raise PermissionDenied
        return form_class(**self.get_form_kwargs(), brand_uuid=brand.id)

    def form_valid(self, form):
        active_locations = form.cleaned_data['location']
        Location.objects.filter(brand__user=self.request.user).update(active=False)
        for active_location_id in active_locations:
            active_location = Location.objects.get(id=active_location_id)
            active_location.active = True
            active_location.save()
        return super().form_valid(form)


class FetchInstaEmbedPost(RegisteredLoginRequiredMixin, View):

    def get(self, request, insta_url_encoded, *args, **kwargs):
        uri = (settings.FACEBOOK_GRAPH_URI +
            f'instagram_oembed?url={force_text(urlsafe_base64_decode(insta_url_encoded))}' +
            f'&access_token={settings.FACEBOOK_KEY}|{settings.FACEBOOK_CLIENT_TOKEN}')
        data = json.loads(requests.get(uri).text)
        return JsonResponse(data)
