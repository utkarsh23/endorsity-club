import json
import requests
import urllib.parse

from django.conf import settings
from django.db.models import Q
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.shortcuts import render
from django.urls import reverse_lazy

from accounts.models import Brand, Location

from brand.forms import AddLocationForm
from brand.mixins import RegisteredBrandLoginRequiredMixin

from notifications.models import Notification


class YourEndorsementsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/your-endorsements.html'


class ProfileView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = Brand.objects.get(user=self.request.user)
        context['brand'] = brand
        context['locations'] = (Location.objects
            .filter(brand=brand))
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
