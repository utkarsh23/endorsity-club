from django.db.models import Q
from django.views.generic.base import TemplateView
from django.shortcuts import render

from brand.mixins import RegisteredBrandLoginRequiredMixin

from notifications.models import Notification


class YourEndorsementsView(RegisteredBrandLoginRequiredMixin, TemplateView):
    template_name = 'brand/your-endorsements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notifications'] = (Notification.objects
            .filter(user=self.request.user)
            .order_by('-created_at'))[:8]
        context['notifs_unread'] = (Notification.objects
            .filter(Q(user=self.request.user) & Q(is_seen=False)).count())
        return context
