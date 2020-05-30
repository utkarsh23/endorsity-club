from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse


class RegisteredBrandLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_brand:
            return redirect(reverse('accounts:landing'))
        if not request.user.is_registered:
            return redirect(reverse('accounts:check_registration'))
        return super().dispatch(request, *args, **kwargs)
