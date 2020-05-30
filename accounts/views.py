import os

from django.conf import settings
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordContextMixin,
)
from django.shortcuts import render, redirect, resolve_url
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
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
    UnregisteredLoginRequiredMixin
)
from accounts.models import (
    Brand,
    FacebookPermissions,
    Influencer,
)
from accounts.utils import (
    center_crop_and_square_image,
    resize_image,
)


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
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
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


class PasswordResetDoneView(PasswordContextMixin, TemplateView):
    template_name = 'accounts/password_reset_done.html'
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
        brand = forms['brand_form'].save(commit=False)
        user = forms['user_form'].save(commit=False)
        user.is_brand = True
        user.is_registered = True
        user.is_google_account = False
        user.save()
        brand.user = user
        brand.save()
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
        user = forms['user_form'].save(commit=False)
        user.is_registered = True
        user.is_google_account = False
        user.save()
        influencer = forms['influencer_form'].save(commit=False)
        influencer.user = user
        influencer.save()
        fb_permissions = FacebookPermissions.objects.create(influencer=influencer)
        return super().forms_valid(forms)


class CheckRegistrationView(UnregisteredLoginRequiredMixin, View):

    def get(self, request):
        if request.user.is_registered:
            return redirect(reverse_lazy('accounts:landing'))
        else:
            return redirect(reverse_lazy('accounts:select_registration'))


class SelectRegistrationView(UnregisteredLoginRequiredMixin, TemplateView):
    template_name = 'accounts/select_registration.html'


class CompleteBrandRegistrationView(UnregisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/complete_brand_reg.html'
    form_class = BrandCreationForm
    success_url = reverse_lazy('accounts:landing')

    def form_valid(self, form):
        brand = form.save(commit=False)
        user = self.request.user
        user.is_brand = True
        user.is_registered = True
        user.save()
        brand.user = user
        brand.save()
        return super().form_valid(form)


class CompleteInfluencerRegistrationView(UnregisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/complete_influencer_reg.html'
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
    template_name = 'accounts/password_change_form.html'
    success_url = reverse_lazy('accounts:password_change_done')


class PasswordChangeDoneView(NoGoogleAuthLoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'


class SettingsView(RegisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/settings.html'
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
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ProfilePictureChangeView(RegisteredLoginRequiredMixin, FormView):
    template_name = 'accounts/profile_picture_change.html'
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
