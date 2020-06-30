from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import (
    PasswordResetForm,
    ReadOnlyPasswordHashField,
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import Brand, Influencer
from accounts.tasks import email_message_async


UserModel = get_user_model()


class AdminUserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = UserModel
        fields = ('email', 'password', 'is_active', 'is_admin', 'is_brand')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = UserModel
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get('password2')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error('password2', error)

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class BrandCreationForm(forms.ModelForm):
    store_location = forms.CharField(max_length=500)

    class Meta(object):
        model = Brand
        fields = ['name', 'phone_number', 'website', 'instagram_handle']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if len(phone_number) != 10:
            raise forms.ValidationError("Please enter a 10-digit phone number.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Please enter all digits only.")
        return phone_number


class InfluencerCreationForm(forms.ModelForm):

    class Meta(object):
        model = Influencer
        fields = ['first_name', 'last_name', 'phone_number']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if len(phone_number) != 10:
            raise forms.ValidationError("Please enter a 10-digit phone number.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Please enter all digits only.")
        return phone_number


class BrandChangeForm(forms.ModelForm):
    store_location = forms.CharField(max_length=500)

    class Meta(object):
        model = Brand
        fields = ['name', 'phone_number', 'website', 'instagram_handle']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if len(phone_number)  != 10:
            raise forms.ValidationError("Please enter a 10-digit phone number.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Please enter all digits only.")
        return phone_number


class InfluencerChangeForm(forms.ModelForm):

    class Meta(object):
        model = Influencer
        fields = ['first_name', 'last_name', 'phone_number']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if len(phone_number) != 10:
            raise forms.ValidationError("Please enter a 10-digit phone number.")
        if not phone_number.isdigit():
            raise forms.ValidationError("Please enter all digits only.")
        return phone_number


class ProfilePictureChangeForm(forms.ModelForm):

    class Meta(object):
        model = UserModel
        fields = ['profile_picture']


class PasswordResetForm(PasswordResetForm):

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        email_field_name = UserModel.get_email_field_name()
        for user in self.get_users(email):
            if not user.is_google_account:
                user_email = getattr(user, email_field_name)
                context = {
                    'email': user_email,
                    'domain': domain,
                    'site_name': site_name,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'user': user,
                    'token': token_generator.make_token(user),
                    'protocol': 'https' if use_https else 'http',
                    **(extra_email_context or {}),
                }
                self.send_mail(
                    subject_template_name, email_template_name, context, from_email,
                    user_email, html_email_template_name=html_email_template_name,
                )

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message_async.delay(email_message)
