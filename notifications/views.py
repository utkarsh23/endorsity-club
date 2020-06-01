from django.views.generic.base import TemplateView

from accounts.mixins import RegisteredLoginRequiredMixin
from accounts.models import Influencer, Brand

from notifications.models import Notification


class NotificationsView(RegisteredLoginRequiredMixin, TemplateView):
    template_name = 'notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_notifications'] = (Notification.objects
            .filter(user=self.request.user)
            .order_by('-created_at'))[:30]
        context['notifications'] = (Notification.objects
            .filter(user=self.request.user)
            .order_by('-created_at'))[:8]
        return context
