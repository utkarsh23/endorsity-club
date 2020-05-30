from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse


class RegisteredLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('accounts:landing'))
        if not request.user.is_registered:
            return redirect(reverse('accounts:check_registration'))
        return super().dispatch(request, *args, **kwargs)


class UnregisteredLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or \
            request.user.is_registered:
            return redirect(reverse('accounts:landing'))
        return super().dispatch(request, *args, **kwargs)


class NoGoogleAuthLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or \
            request.user.is_google_account:
            return redirect(reverse('accounts:landing'))
        return super().dispatch(request, *args, **kwargs)
