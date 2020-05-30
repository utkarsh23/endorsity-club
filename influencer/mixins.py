from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse

from accounts.models import FacebookPermissions, Influencer


# class RegisteredInfluencerLoginRequiredMixin(AccessMixin):
#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated or request.user.is_brand:
#             return redirect(reverse('accounts:landing'))
#         if not request.user.is_registered:
#             return redirect(reverse('accounts:check_registration'))
#         return super().dispatch(request, *args, **kwargs)


class NotFbConnectedInfluencerLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_brand:
            return redirect(reverse('accounts:landing'))
        if not request.user.is_registered:
            return redirect(reverse('accounts:check_registration'))
        influencer = Influencer.objects.get(user=request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        if fb_permissions.has_all_permissions:
            return redirect(reverse('influencer:await_verification'))
        return super().dispatch(request, *args, **kwargs)


class NotVerifiedAndFbConnectedInfluencerLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_brand:
            return redirect(reverse('accounts:landing'))
        if not request.user.is_registered:
            return redirect(reverse('accounts:check_registration'))
        influencer = Influencer.objects.get(user=request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        if not fb_permissions.has_all_permissions:
            return redirect(reverse('influencer:fb_connect'))
        if influencer.is_verified:
            return redirect(reverse('influencer:brands'))
        return super().dispatch(request, *args, **kwargs)


class VerifiedAndFbConnectedInfluencerLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.is_brand:
            return redirect(reverse('accounts:landing'))
        if not request.user.is_registered:
            return redirect(reverse('accounts:check_registration'))
        influencer = Influencer.objects.get(user=request.user)
        fb_permissions = FacebookPermissions.objects.get(influencer=influencer)
        if not fb_permissions.has_all_permissions:
            return redirect(reverse('influencer:fb_connect'))
        if not influencer.is_verified:
            return redirect(reverse('influencer:await_verification'))
        return super().dispatch(request, *args, **kwargs)
