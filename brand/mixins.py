from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


class RegisteredBrandLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('accounts:landing'))
        if not request.user.is_brand:
            raise PermissionDenied
        if not request.user.is_registered:
            return redirect(reverse('accounts:check_registration'))
        if not request.user.is_account_activated:
            return redirect(reverse('accounts:activation_pending'))
        return super().dispatch(request, *args, **kwargs)
