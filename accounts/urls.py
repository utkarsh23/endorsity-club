from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.generic.base import TemplateView

from accounts.views import (
    LandingPageView,
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordChangeView,
    PasswordChangeDoneView,
    SettingsView,
    CheckRegistrationView,
    SelectRegistrationView,
    CompleteBrandRegistrationView,
    CompleteInfluencerRegistrationView,
    ProfilePictureChangeView,
    BrandCreationView,
    InfluencerCreationView,
    NoAuthView,
    AccountExistsView,
)

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy('accounts:password_reset_complete'),
        ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html",
        ), name='password_reset_complete'),
    path('register/brand/', BrandCreationView.as_view(), name='brand_registration'),
    path('register/influencer/', InfluencerCreationView.as_view(), name='influencer_registration'),
    path('register/done/', TemplateView.as_view(
        template_name="accounts/registration_complete.html",
        ), name='registration_complete'),
    path('check-registration/', CheckRegistrationView.as_view(), name="check_registration"),
    path('select-registration/', SelectRegistrationView.as_view(), name="select_registration"),
    path('complete-brand-reg/', CompleteBrandRegistrationView.as_view(), name="complete_brand_reg"),
    path('complete-influencer-reg/', CompleteInfluencerRegistrationView.as_view(), name="complete_influencer_reg"),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('profile_picture_change/', ProfilePictureChangeView.as_view(), name='profile_picture_change'),
    path('account-exists/', AccountExistsView.as_view(), name='account_exists'),
    path('howitworks/', NoAuthView.as_view(template_name='noauth/howitworks.html'), name='how_it_works'),
    path('faq/', NoAuthView.as_view(template_name='noauth/faq.html'), name='faq'),
    path('contactus/', NoAuthView.as_view(template_name='noauth/contactus.html'), name='contact_us'),
]

app_name = 'accounts'
