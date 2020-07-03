import json
import os
import requests
import urllib.parse

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordContextMixin,
)
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q
from django.shortcuts import render, redirect, resolve_url
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView

from multi_form_view import MultiModelFormView

from accounts.forms import (
    PasswordResetForm,
    UserCreationForm,
    BrandCreationForm,
    InfluencerCreationForm,
    BrandChangeForm,
    InfluencerChangeForm,
    ProfilePictureChangeForm,
)
from accounts.mixins import (
    NoGoogleAuthLoginRequiredMixin,
    RegisteredLoginRequiredMixin,
    UnregisteredLoginRequiredMixin,
    NotActivatedLoginRequiredMixin,
)
from accounts.models import (
    Brand,
    Location,
    FacebookPermissions,
    Influencer,
)
from accounts.tasks import send_activation_email
from accounts.tokens import account_activation_token
from accounts.utils import (
    center_crop_and_square_image,
    resize_image,
)

from notifications.models import Notification


user_model = get_user_model()

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    return render(request, 'errors/403.html', status=403)

def handler400(request, exception):
    return render(request, 'errors/400.html', status=400)


class LandingPageView(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if self.request.user.is_brand:
                return redirect(resolve_url(settings.LOGIN_REDIRECT_BRAND_URL))
            else:
                return redirect(resolve_url(settings.LOGIN_REDIRECT_INF_URL))
        
        return render(request, 'noauth/landing.html')


class LoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        url = self.get_redirect_url()
        if url:
            return url
        else:
            if self.request.user.is_brand:
                return resolve_url(settings.LOGIN_REDIRECT_BRAND_URL)
            else:
                return resolve_url(settings.LOGIN_REDIRECT_INF_URL)


class PasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset/password_reset_form.html'
    email_template_name = 'accounts/password_reset/password_reset_email.html'
    subject_template_name = 'accounts/password_reset/password_reset_subject.txt'
    form_class = PasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            redirect_to = resolve_url(
                settings.LOGIN_REDIRECT_BRAND_URL
                if self.request.user.is_brand
                else settings.LOGIN_REDIRECT_INF_URL
            )
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return redirect(redirect_to)
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        try:
            data = {
                'secret': settings.HCAPTCHA_SECRET,
                'response': self.request.POST['h-captcha-response'],
            }
            response = requests.post('https://hcaptcha.com/siteverify', data=data).json()
            if response['success'] == False:
                return self.form_invalid(form)
        except:
            return self.form_invalid(form)
        return super().form_valid(form)


class PasswordResetDoneView(PasswordContextMixin, TemplateView):
    template_name = 'accounts/password_reset/password_reset_done.html'
    title = 'Password reset sent'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            redirect_to = resolve_url(
                settings.LOGIN_REDIRECT_BRAND_URL
                if self.request.user.is_brand
                else settings.LOGIN_REDIRECT_INF_URL
            )
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return redirect(redirect_to)
        context = self.get_context_data()
        return self.render_to_response(context)


class BrandCreationView(MultiModelFormView):
    form_classes = {
        'user_form': UserCreationForm,
        'brand_form': BrandCreationForm,
    }
    record_id = None
    template_name = 'accounts/brand_registration.html'

    def get_success_url(self):
        return reverse_lazy('accounts:registration_complete')
    
    def forms_valid(self, forms):
        store_location = forms['brand_form'].cleaned_data['store_location']
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
            data = {
                'secret': settings.HCAPTCHA_SECRET,
                'response': self.request.POST['h-captcha-response'],
            }
            response = requests.post('https://hcaptcha.com/siteverify', data=data).json()
            if response['success'] == False:
                return self.form_invalid(form)
        except:
            return super().form_invalid(forms)
        user = forms['user_form'].save(commit=False)
        user.is_brand = True
        user.is_registered = True
        user.is_google_account = False
        user.is_account_activated = False
        user.save()
        brand = forms['brand_form'].save(commit=False)
        brand.user = user
        brand.save()
        location = Location.objects.create(
            brand=brand,
            name=store_location,
            latitude=lat_lng['lat'],
            longitude=lat_lng['lng'],
            city=city,
        )
        send_activation_email.delay(user.pk, get_current_site(self.request))
        return super().forms_valid(forms)


class InfluencerCreationView(MultiModelFormView):
    form_classes = {
        'user_form': UserCreationForm,
        'influencer_form': InfluencerCreationForm,
    }
    record_id = None
    template_name = 'accounts/influencer_registration.html'

    def get_success_url(self):
        return reverse_lazy('accounts:registration_complete')
    
    def forms_valid(self, forms):
        try:
            data = {
                'secret': settings.HCAPTCHA_SECRET,
                'response': self.request.POST['h-captcha-response'],
            }
            response = requests.post('https://hcaptcha.com/siteverify', data=data).json()
            if response['success'] == False:
                return self.form_invalid(form)
        except:
            return self.form_invalid(form)
        user = forms['user_form'].save(commit=False)
        user.is_registered = True
        user.is_google_account = False
        user.is_account_activated = False
        user.save()
        influencer = forms['influencer_form'].save(commit=False)
        influencer.user = user
        influencer.save()
        fb_permissions = FacebookPermissions.objects.create(influencer=influencer)
        send_activation_email.delay(user.pk, get_current_site(self.request))
        return super().forms_valid(forms)


class ActivateAccount(View):

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = user_model.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_account_activated = True
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(reverse_lazy('accounts:landing'))
        else:
            return redirect(reverse_lazy('accounts:activation_failed'))


class AuthActivationView(NotActivatedLoginRequiredMixin, TemplateView):
    pass


class ResendActivationMail(NotActivatedLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        send_activation_email.delay(request.user.pk, get_current_site(request))
        return redirect(reverse_lazy('accounts:activation_resend_done'))


class CheckRegistrationView(UnregisteredLoginRequiredMixin, View):

    def get(self, request):
        if request.user.is_registered:
            return redirect(reverse_lazy('accounts:landing'))
        else:
            return redirect(reverse_lazy('accounts:select_registration'))


class SelectRegistrationView(UnregisteredLoginRequiredMixin, TemplateView):
    template_name = 'accounts/complete_registration/select_registration.html'


class CompleteBrandRegistrationView(UnregisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/complete_registration/complete_brand_reg.html'
    form_class = BrandCreationForm
    success_url = reverse_lazy('accounts:landing')

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
        brand = form.save(commit=False)
        user = self.request.user
        user.is_brand = True
        user.is_registered = True
        user.save()
        brand.user = user
        brand.save()
        location = Location.objects.create(
            brand=brand,
            name=store_location,
            latitude=lat_lng['lat'],
            longitude=lat_lng['lng'],
            city=city,
        )
        return super().form_valid(form)


class CompleteInfluencerRegistrationView(UnregisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/complete_registration/complete_influencer_reg.html'
    form_class = InfluencerCreationForm
    success_url = reverse_lazy('accounts:landing')

    def form_valid(self, form):
        user = self.request.user
        user.is_registered = True
        user.save()
        influencer = form.save(commit=False)
        influencer.user = user
        influencer.save()
        fb_permissions = FacebookPermissions.objects.create(influencer=influencer)
        return super().form_valid(form)


class PasswordChangeView(NoGoogleAuthLoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/account_change/password_change_form.html'
    success_url = reverse_lazy('accounts:password_change_done')


class PasswordChangeDoneView(NoGoogleAuthLoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'accounts/account_change/password_change_done.html'


class SettingsView(RegisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/account_change/settings.html'
    success_url = reverse_lazy('accounts:settings')

    def get_form_class(self):
        return (BrandChangeForm
            if self.request.user.is_brand else InfluencerChangeForm)
    
    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        instance = (Brand.objects.get(user=self.request.user)
            if self.request.user.is_brand else
            Influencer.objects.get(user=self.request.user))
        return form_class(**self.get_form_kwargs(), instance=instance)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_registered and self.request.user.is_account_activated:
            if self.request.user.is_brand:
                context['base_template'] = 'brand/base.html'
            else:
                context['base_template'] = 'influencer/base.html'
        else:
            context['base_template'] = 'accounts/noauth/auth_base.html'
        return context
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ProfilePictureChangeView(RegisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/account_change/profile_picture_change.html'
    success_url = reverse_lazy('accounts:profile_picture_change')
    form_class = ProfilePictureChangeForm

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse_lazy('accounts:landing'))
        if not request.user.is_registered:
            return redirect(reverse_lazy('accounts:check_registration'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs(), instance=self.request.user)
    
    def form_valid(self, form):
        user = form.save()
        center_crop_and_square_image(os.path.join(settings.BASE_DIR, user.profile_picture.url[1:]))
        resize_image(os.path.join(settings.BASE_DIR, user.profile_picture.url[1:]))
        return super().form_valid(form)


class NoAuthView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['notifications'] = (Notification.objects
                .filter(user=self.request.user)
                .order_by('-created_at'))[:8]
            context['notifs_unread'] = (Notification.objects
                .filter(Q(user=self.request.user) & Q(is_seen=False)).count())
            base_template = 'noauth/auth_base.html'
        else:
            base_template = 'noauth/base.html'
        context['base_template'] = base_template
        return context


class AccountExistsView(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('accounts:landing'))
        else:
            return render(request, 'accounts/account_exists.html')
