from django.views.generic.base import TemplateView
from django.shortcuts import render

from brand.mixins import RegisteredBrandLoginRequiredMixin


class YourEndorsementsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/your-endorsements.html'
